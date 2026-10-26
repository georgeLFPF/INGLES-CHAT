"""Gerencia o Tutor de Pronúncia: com Docker (via Docker SDK para Python) ou localmente.

Uso:
    python manage.py start   # baixa as imagens, constrói a aplicação e sobe os containers
    python manage.py stop    # para e remove os containers (volumes são mantidos)
    python manage.py local   # roda sem Docker, usando o Ollama instalado na máquina
"""

import argparse
import logging
import os
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import docker
from docker.errors import APIError, BuildError, DockerException, NotFound
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("manage")

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")
REDE = "tutor-net"
VOLUME_MODELOS = "tutor_ollama_models"
VOLUME_DADOS = "tutor_app_data"
IMAGEM_OLLAMA = "ollama/ollama:latest"
IMAGEM_APP = "tutor-pronuncia-app"
CONTAINER_OLLAMA = "tutor-ollama"
CONTAINER_APP = "tutor-app"

MODELO_CHAT = os.getenv("OLLAMA_MODEL", "llama3.1")
MODELO_EMBEDDING = os.getenv("HF_EMBED_MODEL", "Xenova/paraphrase-multilingual-MiniLM-L12-v2")
# Com a chave do Ollama Cloud o modelo roda nos servidores do Ollama: o container local não é usado.
USA_CLOUD = bool(os.getenv("OLLAMA_API_KEY"))


def _rede(client: docker.DockerClient):
    try:
        return client.networks.get(REDE)
    except NotFound:
        log.info("Criando rede %s", REDE)
        return client.networks.create(REDE, driver="bridge")


def _volume(client: docker.DockerClient, nome: str) -> None:
    try:
        client.volumes.get(nome)
    except NotFound:
        log.info("Criando volume %s", nome)
        client.volumes.create(nome)


def _container(client: docker.DockerClient, nome: str):
    try:
        return client.containers.get(nome)
    except NotFound:
        return None


def _garantir_imagem(client: docker.DockerClient, imagem: str, atualizar: bool) -> None:
    # A imagem do Ollama tem alguns GB: só vai ao registry se ela não existir ou se pedirem.
    if not atualizar:
        try:
            client.images.get(imagem)
            return
        except NotFound:
            pass
    log.info("Baixando imagem %s (pode demorar)...", imagem)
    client.images.pull(imagem)


def subir_ollama(client: docker.DockerClient, atualizar: bool = False):
    container = _container(client, CONTAINER_OLLAMA)
    if container is None:
        _garantir_imagem(client, IMAGEM_OLLAMA, atualizar)
        log.info("Criando container %s", CONTAINER_OLLAMA)
        container = client.containers.run(
            IMAGEM_OLLAMA,
            name=CONTAINER_OLLAMA,
            detach=True,
            ports={"11434/tcp": 11434},
            volumes={VOLUME_MODELOS: {"bind": "/root/.ollama", "mode": "rw"}},
            network=REDE,
            restart_policy={"Name": "unless-stopped"},
        )
    else:
        if container.status != "running":
            log.info("Iniciando container %s", CONTAINER_OLLAMA)
            container.start()
        # Um container criado por outro meio (ex.: docker compose) pode estar em outra rede.
        container.reload()
        if REDE not in container.attrs["NetworkSettings"]["Networks"]:
            client.networks.get(REDE).connect(container)
    return container


def esperar_ollama(container, tentativas: int = 60) -> None:
    log.info("Aguardando o Ollama ficar pronto...")
    for _ in range(tentativas):
        if container.exec_run("ollama list").exit_code == 0:
            return
        time.sleep(1)
    raise RuntimeError("O Ollama não respondeu a tempo.")


def baixar_modelo(container, atualizar: bool = False) -> None:
    # O modelo de embeddings vem do Hugging Face e é baixado pela própria aplicação.
    # "ollama pull" sempre consulta o registry; se o modelo já está no volume, pula.
    if not atualizar and container.exec_run(["ollama", "show", MODELO_CHAT]).exit_code == 0:
        log.info("Modelo %s já está baixado.", MODELO_CHAT)
        return
    log.info("Baixando modelo %s (só demora na primeira vez)...", MODELO_CHAT)
    resultado = container.exec_run(f"ollama pull {MODELO_CHAT}")
    if resultado.exit_code != 0:
        raise RuntimeError(
            f"Falha ao baixar {MODELO_CHAT}: {resultado.output.decode(errors='replace')}"
        )


def construir_app(client: docker.DockerClient):
    log.info("Construindo imagem %s...", IMAGEM_APP)
    try:
        imagem, logs = client.images.build(path=str(BASE_DIR), tag=IMAGEM_APP, rm=True)
    except BuildError as e:
        for linha in e.build_log:
            if texto := linha.get("stream", "").strip():
                log.info("  %s", texto)
        # Sem isso o container antigo continuaria rodando o código desatualizado.
        raise RuntimeError(f"Falha ao construir a imagem da aplicação: {e.msg}") from e
    for linha in logs:
        if texto := linha.get("stream", "").strip():
            log.info("  %s", texto)
    return imagem


def verificar_app(client: docker.DockerClient, tentativas: int = 120) -> None:
    """Espera o Streamlit responder e confere, de dentro do container, se ele enxerga o Ollama."""
    log.info("Aguardando o Streamlit ficar pronto...")
    container = client.containers.get(CONTAINER_APP)
    for _ in range(tentativas):
        container.reload()
        if container.status in ("exited", "dead"):
            break
        saude = container.exec_run(
            ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health')"]
        )
        if saude.exit_code == 0:
            break
        time.sleep(1)
    else:
        raise RuntimeError("O Streamlit não respondeu a tempo. Veja: docker logs tutor-app")

    if container.status != "running":
        logs = container.logs(tail=40).decode(errors="replace")
        raise RuntimeError(f"O container {CONTAINER_APP} parou ao iniciar. Últimos logs:\n{logs}")

    # Mesma checagem que o agente faz ao abrir a página, mas aqui o erro aparece no terminal.
    teste = container.exec_run(
        ["python", "-c", "from agent import _cliente_ollama, verificar_modelos, MODELO_CHAT; "
         "verificar_modelos(_cliente_ollama(), MODELO_CHAT)"],
        workdir="/app",
    )
    if teste.exit_code != 0:
        raise RuntimeError(
            f"A aplicação não conseguiu falar com o Ollama:\n{teste.output.decode(errors='replace')}"
        )
    log.info("Streamlit conectado ao Ollama (%s).", MODELO_CHAT)


def _ambiente_app() -> dict[str, str]:
    return {
        "OLLAMA_HOST": f"http://{CONTAINER_OLLAMA}:11434",
        "OLLAMA_MODEL": MODELO_CHAT,
        "HF_EMBED_MODEL": MODELO_EMBEDDING,
        "HF_TOKEN": os.getenv("HF_TOKEN", ""),
        "HF_HOME": "/app/storage/huggingface",
        "OLLAMA_API_KEY": os.getenv("OLLAMA_API_KEY", ""),
        "DB_PATH": "/app/storage/progresso.db",
        "CHROMA_DIR": "/app/storage/.chroma",
    }


def subir_app(client: docker.DockerClient, imagem) -> None:
    ambiente = _ambiente_app()
    if antigo := _container(client, CONTAINER_APP):
        # Nada mudou (mesma imagem e mesmas variáveis): mantém o container que já está rodando.
        env_atual = set(antigo.attrs["Config"]["Env"] or [])
        if (
            antigo.status == "running"
            and antigo.image.id == imagem.id
            and {f"{k}={v}" for k, v in ambiente.items()} <= env_atual
        ):
            log.info("Container %s já está atualizado, mantendo.", CONTAINER_APP)
            return
        antigo.remove(force=True)
    log.info("Criando container %s", CONTAINER_APP)
    client.containers.run(
        IMAGEM_APP,
        name=CONTAINER_APP,
        detach=True,
        ports={"8501/tcp": 8501},
        environment=ambiente,
        volumes={VOLUME_DADOS: {"bind": "/app/storage", "mode": "rw"}},
        network=REDE,
        restart_policy={"Name": "unless-stopped"},
    )


def _preparar_ollama(client: docker.DockerClient, atualizar: bool) -> None:
    ollama = subir_ollama(client, atualizar)
    esperar_ollama(ollama)
    baixar_modelo(ollama, atualizar)


def start(client: docker.DockerClient, atualizar: bool = False) -> None:
    _rede(client)
    _volume(client, VOLUME_MODELOS)
    _volume(client, VOLUME_DADOS)
    # O build da aplicação não depende do Ollama: roda em paralelo com a subida e os modelos.
    # Cliente próprio na thread, para não compartilhar a sessão HTTP entre threads.
    with ThreadPoolExecutor(max_workers=1) as executor:
        build = executor.submit(construir_app, docker.from_env())
        if USA_CLOUD:
            log.info("Usando o Ollama Cloud (%s): o Ollama local não será iniciado.", MODELO_CHAT)
            # Libera a RAM caso o Ollama local tenha ficado de uma execução anterior.
            if (local := _container(client, CONTAINER_OLLAMA)) and local.status == "running":
                log.info("Parando container %s", CONTAINER_OLLAMA)
                local.stop()
        else:
            _preparar_ollama(client, atualizar)
        imagem = build.result()
    subir_app(client, imagem)
    verificar_app(client)
    log.info("\nPronto! Acesse http://localhost:8501")


def stop(client: docker.DockerClient) -> None:
    for nome in (CONTAINER_APP, CONTAINER_OLLAMA):
        if container := _container(client, nome):
            log.info("Removendo container %s", nome)
            container.remove(force=True)
    log.info("Containers parados. Os volumes (modelos e histórico) foram mantidos.")


def _ollama_respondendo(host: str) -> bool:
    try:
        urllib.request.urlopen(f"{host}/api/version", timeout=2)
        return True
    except OSError:
        return False


def subir_ollama_local(host: str, tentativas: int = 30) -> subprocess.Popen | None:
    """Usa o Ollama que já está rodando; se não houver, inicia `ollama serve` em segundo plano."""
    if _ollama_respondendo(host):
        log.info("Ollama já está rodando em %s", host)
        return None
    executavel = shutil.which("ollama")
    if executavel is None:
        raise RuntimeError(
            "O Ollama não foi encontrado. Instale em https://ollama.com ou use `python manage.py start` (Docker)."
        )
    log.info("Iniciando `ollama serve`...")
    processo = subprocess.Popen(
        [executavel, "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    for _ in range(tentativas):
        if _ollama_respondendo(host):
            return processo
        time.sleep(1)
    processo.terminate()
    raise RuntimeError(f"O Ollama não respondeu em {host} a tempo.")


def local() -> None:
    """Roda a aplicação direto na máquina, sem Docker."""
    # Importados aqui: dependem do .env já carregado e só são usados neste modo.
    from agent import _cliente_ollama, verificar_modelos

    nuvem = bool(os.getenv("OLLAMA_API_KEY"))
    host = os.getenv("OLLAMA_HOST") or "http://127.0.0.1:11434"
    ollama_local = None if nuvem else subir_ollama_local(host)
    try:
        cliente = _cliente_ollama()
        if not nuvem:
            # Os modelos do Ollama Cloud já estão disponíveis; só os locais precisam de pull.
            for modelo in dict.fromkeys((MODELO_CHAT, MODELO_ANALISE)):
                log.info("Baixando modelo %s (só demora na primeira vez)...", modelo)
                cliente.pull(modelo)
        verificar_modelos(cliente, MODELO_CHAT, MODELO_ANALISE)
        log.info("Ollama pronto (%s, %s). Iniciando o Streamlit...", MODELO_CHAT, MODELO_ANALISE)
        log.info("Acesse http://localhost:8501  (Ctrl+C para parar)\n")
        try:
            subprocess.run(
                [sys.executable, "-m", "streamlit", "run", str(BASE_DIR / "front-end" / "app.py"),
                 "--server.port=8501"],
                cwd=BASE_DIR,
                check=False,
            )
        except KeyboardInterrupt:
            pass
    finally:
        # Só encerra o Ollama se foi este script que o iniciou.
        if ollama_local is not None:
            log.info("Encerrando o Ollama iniciado por este script.")
            ollama_local.terminate()


def main() -> int:
    parser = argparse.ArgumentParser(description="Gerencia o Tutor de Pronúncia (Docker ou local).")
    comandos = parser.add_subparsers(dest="comando", required=True, metavar="{start,stop,local}")
    comandos.add_parser("start", help="baixa as imagens, constrói a aplicação e sobe os containers")
    comandos.add_parser("stop", help="para e remove os containers (volumes são mantidos)")
    comandos.add_parser("local", help="roda sem Docker, usando o Ollama instalado na máquina")
    args = parser.parse_args()

    if args.comando == "local":
        try:
            local()
        except Exception as e:  # ollama.ResponseError, ConnectionError, RuntimeError...
            log.error("Erro: %s", e)
            return 1
        return 0

    try:
        client = docker.from_env()
        client.ping()
    except DockerException as e:
        log.error("Não foi possível conectar ao Docker. O Docker Desktop está aberto?\n%s", e)
        return 1

    try:
        if args.comando == "start":
            start(client, args.atualizar)
        else:
            stop(client)
    except (APIError, DockerException, RuntimeError) as e:
        log.error("Erro: %s", e)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
