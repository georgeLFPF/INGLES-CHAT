"""Interface Streamlit do Tutor de Pronúncia."""

import sys
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parent.parent

# Lê as variáveis do .env (se existir) antes de importar o agente, que as usa ao carregar.
load_dotenv(RAIZ / ".env")

# Permite importar os módulos do back-end que ficam na raiz do projeto.
sys.path.insert(0, str(RAIZ))

from agent import Agente  # noqa: E402

st.set_page_config(page_title="Tutor de Pronúncia", page_icon="🗣️", layout="centered")


# Um agente por sessão do navegador, para que a memória de curto prazo não seja compartilhada.
if "agente" not in st.session_state:
    try:
        with st.spinner("Preparando o tutor..."):
            st.session_state.agente = Agente()
    except Exception as e:
        st.error(
            "Não foi possível iniciar o tutor. Verifique se o Ollama está rodando e se há "
            f"internet para baixar o modelo de embeddings na primeira vez.\n\n`{e}`"
        )
        st.stop()
    st.session_state.chat = []
    st.session_state.cartao = None

agente: Agente = st.session_state.agente


def mostrar_cartao(cartao: dict) -> None:
    if "erro" in cartao:
        st.warning(cartao["erro"])
        if cartao.get("bruto"):
            with st.expander("Resposta do modelo"):
                st.write(cartao["bruto"])
        return
    with st.container(border=True):
        st.markdown(f"## {cartao.get('ingles', '')}")
        if cartao.get("portugues"):
            st.caption(f"Português: {cartao['portugues']}")
        if analise := cartao.get("analise"):
            detalhes = [analise.get("classe"), analise.get("observacao")]
            if texto := " · ".join(d for d in detalhes if d):
                st.caption(f"🔎 Análise: {texto}")
        col1, col2 = st.columns(2)
        col1.metric("IPA", cartao.get("ipa", "-"))
        col2.metric("Pronúncia", cartao.get("pronuncia", "-"))
        if cartao.get("dica"):
            st.info(f"💡 **Dica:** {cartao['dica']}")
        if cartao.get("exemplo"):
            st.markdown(f"**Exemplo:** {cartao['exemplo']}")
            if cartao.get("exemplo_pronuncia"):
                st.markdown(f"→ *{cartao['exemplo_pronuncia']}*")


# ---------- Barra lateral: histórico ----------
with st.sidebar:
    st.header("📚 Palavras estudadas")
    try:
        palavras = agente.chamar_tool("listar_palavras").get("palavras", [])
    except Exception as e:
        palavras = []
        st.caption(f"Histórico indisponível: {e}")
    if palavras:
        for p in palavras:
            traducao = f" — {p['portugues']}" if p.get("portugues") else ""
            st.markdown(f"**{p['ingles']}** {p.get('ipa') or ''}{traducao}")
    else:
        st.caption("Nenhuma palavra ainda.")
    st.divider()
    if st.button("Limpar conversa"):
        agente.memoria.limpar()
        st.session_state.chat = []
        st.session_state.cartao = None
        st.rerun()

# ---------- Cartão de pronúncia ----------
st.title("🗣️ Tutor de Pronúncia de Inglês")
st.write("Digite uma palavra em português ou inglês e veja como pronunciar.")

with st.form("form_palavra", clear_on_submit=False):
    palavra = st.text_input("Palavra", placeholder="ex.: cachorro ou thought", max_chars=40)
    enviar = st.form_submit_button("Pronunciar", type="primary")

if enviar:
    if not palavra.strip():
        st.warning("Digite uma palavra.")
    else:
        with st.spinner("Consultando o tutor..."):
            try:
                st.session_state.cartao = agente.pronunciar(palavra)
            except Exception as e:
                st.session_state.cartao = {"erro": f"Erro ao consultar o modelo: {e}"}
        st.rerun()

if st.session_state.cartao:
    mostrar_cartao(st.session_state.cartao)

# ---------- Chat ----------
st.divider()
st.subheader("💬 Dúvidas")
for msg in st.session_state.chat:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if pergunta := st.chat_input("Ex.: me dá rimas, quantas sílabas tem?"):
    st.session_state.chat.append({"role": "user", "content": pergunta})
    with st.chat_message("user"):
        st.markdown(pergunta)
    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            try:
                resposta = agente.conversar(pergunta)
            except Exception as e:
                resposta = f"Erro ao consultar o modelo: {e}"
        st.markdown(resposta)
    st.session_state.chat.append({"role": "assistant", "content": resposta})
