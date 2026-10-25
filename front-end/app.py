"""Interface Streamlit do Tutor de Pronúncia."""

import html
import json
import logging
import sys
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parent.parent

# Lê as variáveis do .env (se existir) antes de importar o agente, que as usa ao carregar.
load_dotenv(RAIZ / ".env")
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

# Permite importar os módulos do back-end que ficam na raiz do projeto.
sys.path.insert(0, str(RAIZ))

from agent import Agente  # noqa: E402
from visual import AVATAR_ALUNO, AVATAR_PROFESSOR, BANDEIRA_BR, BANDEIRA_UK, fundo_sala  # noqa: E402

st.set_page_config(page_title="Tutor de Pronúncia", page_icon="🗣️", layout="centered")


# ---------- Visual: temas ----------

TEMAS = {
    "claro": {
        "fundo": "#F4F7FB",
        "fundo_brilho": "rgba(0,156,59,.10)",
        "fundo_brilho2": "rgba(1,33,105,.10)",
        "superficie": "#FFFFFF",
        "superficie2": "#F1F4F9",
        "texto": "#0F1B2D",
        "suave": "#5B6B82",
        "borda": "#E2E8F0",
        "verde": "#009C3B",
        "amarelo": "#F5C400",
        "azul": "#012169",
        "vermelho": "#C8102E",
        "destaque": "#0B5FFF",
        "sombra": "0 10px 30px rgba(15,27,45,.08)",
        "veu": "rgba(244,247,251,.86)",
        "veu_lados": "rgba(244,247,251,.35)",
    },
    "escuro": {
        "fundo": "#0B1220",
        "fundo_brilho": "rgba(34,197,94,.12)",
        "fundo_brilho2": "rgba(91,141,239,.14)",
        "superficie": "#131C2E",
        "superficie2": "#1B263D",
        "texto": "#E8EEF8",
        "suave": "#94A3BC",
        "borda": "#26334F",
        "verde": "#2ECC71",
        "amarelo": "#FFD93D",
        "azul": "#7AA2FF",
        "vermelho": "#FF5C7A",
        "destaque": "#7AA2FF",
        "sombra": "0 10px 30px rgba(0,0,0,.35)",
        "veu": "rgba(11,18,32,.86)",
        "veu_lados": "rgba(11,18,32,.40)",
    },
}


def aplicar_tema(nome: str) -> dict:
    t = TEMAS[nome]
    variaveis = ";".join(f"--{k.replace('_', '-')}:{v}" for k, v in t.items())
    st.markdown(
        f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500&display=swap');
:root {{ {variaveis}; color-scheme: {"dark" if nome == "escuro" else "light"}; }}

/* Base */
[data-testid="stApp"] {{
  /* Sala de aula ao fundo; o véu é mais forte no centro para o conteúdo continuar legível. */
  background:
    linear-gradient(90deg, var(--veu-lados) 0%, var(--veu) calc(50% - 440px),
      var(--veu) calc(50% + 440px), var(--veu-lados) 100%),
    url("{fundo_sala(nome)}") center bottom / cover no-repeat,
    var(--fundo);
  color: var(--texto);
}}
[data-testid="stAppViewContainer"], [data-testid="stMain"] {{ background: transparent; }}

/* Pop-up de boas-vindas */
div[role="dialog"] {{ background: var(--superficie) !important; border: 1px solid var(--borda); border-radius: 22px !important; }}
div[role="dialog"] p, div[role="dialog"] li, div[role="dialog"] h2, div[role="dialog"] div, div[role="dialog"] b {{ color: var(--texto); }}
div[role="dialog"] button[aria-label="Close"] svg {{ fill: var(--suave); color: var(--suave); }}
div[role="dialog"] [data-testid="stBaseButton-primary"] p {{ color: #fff !important; }}
.boas-vindas .bandeiras {{ justify-content: center; margin: .2rem 0 1rem; }}
.boas-vindas p {{ margin: 0 0 .9rem; color: var(--suave) !important; text-align: center; }}
.passo {{ display: flex; gap: .7rem; align-items: flex-start; background: var(--superficie2);
  border: 1px solid var(--borda); border-radius: 14px; padding: .6rem .8rem; margin-bottom: .5rem; font-size: .93rem; }}
.passo .num {{ flex-shrink: 0; width: 1.6rem; height: 1.6rem; border-radius: 50%; display: grid; place-items: center;
  background: var(--verde); color: #fff !important; font-weight: 800; font-size: .85rem; }}
.boas-vindas .rodape {{ font-size: .8rem; color: var(--suave) !important; text-align: center; margin-top: .8rem; }}
[data-testid="stApp"], [data-testid="stApp"] p, [data-testid="stApp"] label, [data-testid="stApp"] li,
[data-testid="stApp"] h1, [data-testid="stApp"] h2, [data-testid="stApp"] h3,
[data-testid="stApp"] input, [data-testid="stApp"] textarea, [data-testid="stApp"] button {{
  font-family: 'Plus Jakarta Sans', system-ui, -apple-system, 'Segoe UI', sans-serif;
}}
[data-testid="stApp"] p, [data-testid="stApp"] label, [data-testid="stApp"] li,
[data-testid="stApp"] h1, [data-testid="stApp"] h2, [data-testid="stApp"] h3,
[data-testid="stWidgetLabel"], [data-testid="stSpinner"], [data-testid="stCaptionContainer"] {{
  color: var(--texto);
}}
[data-testid="stCaptionContainer"] {{ color: var(--suave); }}
[data-testid="stHeader"] {{ background: transparent; }}
.block-container {{ padding-top: 2.5rem; max-width: 780px; }}

/* Barra lateral */
[data-testid="stSidebar"] {{ background: var(--superficie); border-right: 1px solid var(--borda); }}
[data-testid="stSidebar"] button {{
  background: var(--superficie2); color: var(--texto); border: 1px solid var(--borda); border-radius: 12px;
}}
[data-testid="stSidebar"] button:hover {{ border-color: var(--vermelho); color: var(--vermelho); }}

/* Formulário e campos */
[data-testid="stForm"] {{
  background: var(--superficie); border: 1px solid var(--borda); border-radius: 20px;
  box-shadow: var(--sombra); padding: 1.2rem 1.4rem;
}}
[data-baseweb="input"], [data-baseweb="input"] > div, [data-baseweb="textarea"] {{
  background: var(--superficie2) !important; border-color: var(--borda) !important; border-radius: 12px !important;
}}
[data-baseweb="input"] input, [data-baseweb="textarea"] textarea {{ color: var(--texto) !important; caret-color: var(--verde); }}
[data-baseweb="input"]:focus-within {{ border-color: var(--verde) !important; }}
button[kind="primary"], [data-testid="baseButton-primary"], [data-testid="stBaseButton-primary"],
[data-testid="stFormSubmitButton"] button {{
  background: linear-gradient(135deg, var(--verde), #0A7E3A) !important; color: #fff !important;
  border: none !important; border-radius: 12px !important; font-weight: 700 !important;
  padding: .55rem 1.4rem !important; box-shadow: 0 6px 16px rgba(0,156,59,.28);
  transition: transform .15s ease, box-shadow .15s ease;
}}
[data-testid="stFormSubmitButton"] button p {{ color: #fff !important; }}
[data-testid="stFormSubmitButton"] button:hover {{ transform: translateY(-1px); box-shadow: 0 10px 22px rgba(0,156,59,.35); }}

/* Chat */
[data-testid="stChatMessage"] {{
  background: var(--superficie); border: 1px solid var(--borda); border-radius: 16px; padding: .8rem 1rem;
}}
[data-testid="stBottom"], [data-testid="stBottom"] > div, [data-testid="stBottomBlockContainer"] {{ background: var(--fundo) !important; }}
[data-testid="stChatInput"] {{ background: var(--superficie2) !important; border: 1px solid var(--borda) !important; border-radius: 16px !important; }}
[data-testid="stChatInput"] > div {{ background: transparent !important; }}
[data-testid="stExpander"] details {{ background: var(--superficie); border-color: var(--borda); border-radius: 12px; }}
hr {{ border-color: var(--borda) !important; }}

/* Cabeçalho */
.faixa {{ height: 6px; border-radius: 99px; margin-bottom: 1.4rem;
  background: linear-gradient(90deg, #009C3B 0 25%, #FFDF00 25% 50%, #012169 50% 75%, #C8102E 75%); }}
.hero {{ display: flex; align-items: center; gap: 1.1rem; margin-bottom: .4rem; }}
.bandeiras {{ display: flex; align-items: center; gap: .35rem; flex-shrink: 0; }}
.bandeira {{ display: inline-flex; width: 46px; height: 32px; border-radius: 8px; overflow: hidden;
  box-shadow: 0 4px 12px rgba(0,0,0,.18); border: 2px solid var(--superficie); }}
.bandeira svg {{ width: 100%; height: 100%; display: block; }}
.bandeira.mini {{ width: 22px; height: 15px; border-radius: 4px; border-width: 1px; box-shadow: none; vertical-align: -2px; }}
.seta {{ color: var(--suave); font-weight: 800; font-size: 1.1rem; }}
.hero h1 {{ margin: 0 !important; padding: 0 !important; font-size: 2rem !important; font-weight: 800 !important;
  letter-spacing: -.02em; line-height: 1.15 !important; }}
.hero h1 span {{ background: linear-gradient(90deg, var(--verde), var(--destaque)); -webkit-background-clip: text;
  background-clip: text; color: transparent; }}
p.subtitulo {{ color: var(--suave); margin: .2rem 0 1.4rem; font-size: 1.02rem; }}
.secao {{ display: flex; align-items: center; gap: .5rem; font-weight: 800; font-size: 1.15rem;
  color: var(--texto); margin: 1.6rem 0 .8rem; }}

/* Cartão de pronúncia */
.cartao {{ background: var(--superficie); border: 1px solid var(--borda); border-radius: 22px;
  box-shadow: var(--sombra); padding: 1.5rem 1.6rem; margin: 1.2rem 0 .6rem; position: relative; overflow: hidden;
  animation: surgir .35s ease-out; }}
.cartao::before {{ content: ""; position: absolute; inset: 0 0 auto 0; height: 5px;
  background: linear-gradient(90deg, var(--verde), var(--amarelo), var(--azul), var(--vermelho)); }}
@keyframes surgir {{ from {{ opacity: 0; transform: translateY(8px); }} to {{ opacity: 1; transform: none; }} }}
.cartao .etiqueta {{ display: inline-flex; align-items: center; gap: .4rem; font-size: .75rem; font-weight: 700;
  text-transform: uppercase; letter-spacing: .08em; color: var(--suave); }}
.cartao .palavra {{ font-size: 2.6rem; font-weight: 800; letter-spacing: -.02em; color: var(--texto); line-height: 1.1;
  margin: .3rem 0 .2rem; }}
.cartao .traducao {{ display: flex; align-items: center; gap: .45rem; color: var(--suave); font-size: 1rem; }}
.cartao .analise {{ color: var(--suave); font-size: .85rem; margin-top: .5rem; }}
.cartao .grade {{ display: grid; grid-template-columns: 1fr 1fr; gap: .8rem; margin: 1.2rem 0 1rem; }}
.cartao .bloco {{ background: var(--superficie2); border: 1px solid var(--borda); border-radius: 16px; padding: .9rem 1rem; }}
.cartao .bloco.destaque {{ border-color: var(--verde); background:
  linear-gradient(135deg, var(--fundo-brilho), transparent), var(--superficie2); }}
.cartao .rotulo {{ display: block; font-size: .72rem; font-weight: 700; text-transform: uppercase;
  letter-spacing: .08em; color: var(--suave); margin-bottom: .3rem; }}
.cartao .valor {{ display: block; font-size: 1.45rem; font-weight: 700; color: var(--texto); word-break: break-word; }}
.cartao .valor.ipa {{ font-family: 'JetBrains Mono', ui-monospace, monospace; font-size: 1.3rem; color: var(--destaque); }}
.cartao .dica {{ background: rgba(245,196,0,.12); border-left: 4px solid var(--amarelo); border-radius: 12px;
  padding: .8rem 1rem; color: var(--texto); margin-bottom: 1rem; }}
.cartao .exemplo {{ border-top: 1px dashed var(--borda); padding-top: .9rem; color: var(--texto); }}
.cartao .exemplo em {{ display: block; color: var(--suave); margin-top: .2rem; }}
@media (max-width: 520px) {{
  .cartao .grade {{ grid-template-columns: 1fr; }}
  .hero h1 {{ font-size: 1.55rem !important; }}
  .cartao .palavra {{ font-size: 2.1rem; }}
}}

/* Histórico */
.chip {{ display: flex; justify-content: space-between; align-items: baseline; gap: .5rem;
  background: var(--superficie2); border: 1px solid var(--borda); border-radius: 12px;
  padding: .5rem .75rem; margin-bottom: .45rem; }}
.chip b {{ color: var(--texto); }}
.chip small {{ color: var(--suave); font-family: 'JetBrains Mono', ui-monospace, monospace; font-size: .75rem; }}
.chip span {{ color: var(--suave); font-size: .82rem; }}
p.ajuda {{ color: var(--suave); margin: -.3rem 0 .6rem; font-size: .95rem; }}
.sugestoes {{ display: flex; flex-wrap: wrap; gap: .45rem; margin-bottom: 1rem; }}
.sugestoes span {{ background: var(--superficie); border: 1px solid var(--borda); color: var(--texto);
  border-radius: 999px; padding: .35rem .8rem; font-size: .85rem; }}
.vazio {{ color: var(--suave); font-size: .9rem; text-align: center; padding: 1rem .5rem;
  border: 1px dashed var(--borda); border-radius: 12px; }}
[data-testid="stSidebar"] .chip {{ margin-bottom: 0; align-items: center; }}
[class*="st-key-restaurar"] button {{ background: var(--verde); color: #fff; border: none; border-radius: 10px;
  min-height: 2.35rem; font-weight: 800; box-shadow: 0 4px 10px rgba(0,156,59,.25); }}
[class*="st-key-restaurar"] button p {{ color: #fff; font-size: 1.1rem; }}
[class*="st-key-restaurar"] button:hover {{ background: #0A7E3A; color: #fff; transform: translateY(-1px); }}
</style>""",
        unsafe_allow_html=True,
    )
    return t


def bandeira(svg: str, mini: bool = False) -> str:
    return f'<span class="bandeira{" mini" if mini else ""}">{svg}</span>'


# ---------- Estado da sessão ----------

if "tema_escuro" not in st.session_state:
    st.session_state.tema_escuro = False

tema = aplicar_tema("escuro" if st.session_state.tema_escuro else "claro")


@st.dialog("👋 Bem-vindo ao Tutor de Pronúncia!", width="small")
def boas_vindas() -> None:
    passos = [
        "Digite uma palavra em <b>português ou inglês</b>, como <i>cachorro</i> ou <i>thought</i>.",
        "Veja o <b>IPA</b>, a pronúncia do jeito brasileiro, uma dica e uma frase de exemplo, e clique em 🔊 para ouvir.",
        "Pergunte no <b>chat</b> o que quiser sobre a palavra: rimas, sílabas, outros exemplos...",
        "Na barra lateral, o botão verde <b>↺</b> traz de volta uma palavra que você já estudou.",
    ]
    st.markdown(
        '<div class="boas-vindas">'
        f'<div class="bandeiras">{bandeira(BANDEIRA_BR)}<span class="seta">⇄</span>{bandeira(BANDEIRA_UK)}</div>'
        "<p>Um professor de inglês com IA feito para brasileiros: ele mostra como cada palavra soa "
        "e explica por quê.</p>"
        + "".join(f'<div class="passo"><span class="num">{i}</span><div>{p}</div></div>' for i, p in enumerate(passos, 1))
        + '<div class="rodape">Por trás: regras de pronúncia (RAG), memória da conversa e ferramentas MCP.</div>'
        "</div>",
        unsafe_allow_html=True,
    )
    if st.button("Começar a praticar 🚀", type="primary", use_container_width=True):
        st.rerun()


# Mostra o pop-up só na primeira vez que a página abre nesta sessão.
if "boas_vindas" not in st.session_state:
    st.session_state.boas_vindas = True
    boas_vindas()

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
    # Cartões já gerados nesta sessão, para restaurar uma palavra sem chamar o modelo de novo.
    st.session_state.cartoes = {}

agente: Agente = st.session_state.agente


def botao_ouvir(cartao: dict) -> None:
    """Botões que leem a palavra e o exemplo em voz alta (síntese de voz do navegador)."""
    falas = [("🔊 Ouvir palavra", cartao.get("ingles"))]
    if cartao.get("exemplo"):
        falas.append(("🔊 Ouvir exemplo", cartao["exemplo"]))
    botoes = "".join(
        f'<button onclick=\'falar({html.escape(json.dumps(texto))})\'>{rotulo}</button>'
        for rotulo, texto in falas
        if texto
    )
    # st.iframe substitui components.html nas versões novas; o texto do modelo já vai escapado.
    conteudo = (
        f"""<style>
body {{ margin: 0; font-family: 'Plus Jakarta Sans', system-ui, 'Segoe UI', sans-serif; }}
button {{ background: {tema["superficie"]}; color: {tema["texto"]}; border: 1px solid {tema["borda"]};
  border-radius: 999px; padding: .45rem 1rem; margin-right: .4rem; font-weight: 600; font-size: .9rem;
  cursor: pointer; transition: all .15s ease; }}
button:hover {{ border-color: {tema["verde"]}; color: {tema["verde"]}; transform: translateY(-1px); }}
</style>
{botoes}
<script>
function falar(texto) {{
  const fala = new SpeechSynthesisUtterance(texto);
  fala.lang = "en-US";
  fala.rate = 0.85;
  speechSynthesis.cancel();
  speechSynthesis.speak(fala);
}}
</script>"""
    )
    if hasattr(st, "iframe"):
        st.iframe(conteudo, height=46)
    else:
        components.html(conteudo, height=46)


def guardar_cartao(cartao: dict) -> None:
    st.session_state.cartao = cartao
    if cartao.get("ingles"):
        st.session_state.cartoes[cartao["ingles"].strip().lower()] = cartao


def restaurar(palavra: dict) -> None:
    """Volta a mostrar o cartão de uma palavra do histórico e a coloca como assunto do chat."""
    chave = palavra["ingles"].strip().lower()
    if cartao := st.session_state.cartoes.get(chave):
        agente.memoria.registrar_palavra(chave)
        agente.memoria.adicionar("user", f"Quero revisar a palavra '{chave}'.")
        agente.memoria.adicionar("assistant", f"{chave} {cartao.get('ipa', '')} = {cartao.get('pronuncia', '')}")
        st.session_state.cartao = cartao
        return
    # Palavra de outra sessão: o cartão completo não fica salvo, então é gerado de novo.
    with st.spinner(f"Restaurando '{chave}'..."):
        try:
            guardar_cartao(agente.pronunciar(chave))
        except Exception as e:
            st.session_state.cartao = {"erro": f"Erro ao consultar o modelo: {e}"}


def mostrar_cartao(cartao: dict) -> None:
    if cartao.get("aviso_analise"):
        st.warning(cartao["aviso_analise"])
    if "erro" in cartao:
        st.warning(cartao["erro"])
        if cartao.get("bruto"):
            with st.expander("Resposta do modelo"):
                st.write(cartao["bruto"])
        return

    # Tudo que vem do modelo é escapado antes de entrar no HTML.
    e = lambda chave: html.escape(str(cartao.get(chave) or ""))  # noqa: E731
    partes = [
        '<div class="cartao">',
        f'<span class="etiqueta">{bandeira(BANDEIRA_UK, mini=True)} English</span>',
        f'<div class="palavra">{e("ingles")}</div>',
    ]
    if cartao.get("portugues"):
        partes.append(f'<div class="traducao">{bandeira(BANDEIRA_BR, mini=True)} {e("portugues")}</div>')
    if analise := cartao.get("analise"):
        detalhes = [analise.get("classe"), analise.get("observacao")]
        if texto := " · ".join(d for d in detalhes if d):
            partes.append(f'<div class="analise">🔎 {html.escape(texto)}</div>')
    partes += [
        '<div class="grade">',
        f'<div class="bloco"><span class="rotulo">IPA</span><span class="valor ipa">{e("ipa") or "-"}</span></div>',
        '<div class="bloco destaque"><span class="rotulo">Como falar</span>'
        f'<span class="valor">{e("pronuncia") or "-"}</span></div>',
        "</div>",
    ]
    if cartao.get("dica"):
        partes.append(f'<div class="dica">💡 <b>Dica:</b> {e("dica")}</div>')
    if cartao.get("exemplo"):
        pronuncia = f"<em>→ {e('exemplo_pronuncia')}</em>" if cartao.get("exemplo_pronuncia") else ""
        partes.append(f'<div class="exemplo"><b>Exemplo:</b> {e("exemplo")}{pronuncia}</div>')
    partes.append("</div>")
    # Sem quebras de linha: o markdown trataria linhas indentadas como bloco de código.
    st.markdown("".join(partes), unsafe_allow_html=True)
    botao_ouvir(cartao)


# ---------- Barra lateral: tema e histórico ----------
with st.sidebar:
    st.toggle("🌙 Modo escuro", key="tema_escuro")
    st.markdown('<div class="secao">📚 Palavras estudadas</div>', unsafe_allow_html=True)
    try:
        palavras = agente.chamar_tool("listar_palavras").get("palavras", [])
    except Exception as e:
        palavras = []
        st.caption(f"Histórico indisponível: {e}")
    # O histórico guarda cada consulta; aqui cada palavra aparece uma vez só.
    unicas = list({p["ingles"].strip().lower(): p for p in reversed(palavras)}.values())[::-1]
    for i, p in enumerate(unicas):
        col_chip, col_botao = st.columns([5, 1], vertical_alignment="center", gap="small")
        col_chip.markdown(
            f'<div class="chip"><div><b>{html.escape(p["ingles"])}</b> '
            f'<small>{html.escape(p.get("ipa") or "")}</small></div>'
            f'<span>{html.escape(p.get("portugues") or "")}</span></div>',
            unsafe_allow_html=True,
        )
        if col_botao.button("↺", key=f"restaurar_{i}", help=f"Restaurar a sessão de '{p['ingles']}'"):
            restaurar(p)
            st.rerun()
    if not unicas:
        st.markdown('<div class="vazio">Nenhuma palavra ainda.<br>Que tal começar? ✨</div>', unsafe_allow_html=True)
    st.divider()
    if st.button("🧹 Limpar conversa", use_container_width=True):
        agente.memoria.limpar()
        st.session_state.chat = []
        st.session_state.cartao = None
        st.rerun()

# ---------- Cabeçalho ----------
st.markdown(
    '<div class="faixa"></div>'
    '<div class="hero">'
    f'<div class="bandeiras">{bandeira(BANDEIRA_BR)}<span class="seta">⇄</span>{bandeira(BANDEIRA_UK)}</div>'
    "<h1>Tutor de <span>Pronúncia</span></h1>"
    "</div>"
    '<p class="subtitulo">Digite uma palavra em português ou inglês e aprenda a falar como um nativo. 🎯</p>',
    unsafe_allow_html=True,
)

# ---------- Cartão de pronúncia ----------
with st.form("form_palavra", clear_on_submit=False):
    col_campo, col_botao = st.columns([4, 1], vertical_alignment="bottom")
    palavra = col_campo.text_input("Palavra", placeholder="ex.: cachorro ou thought", max_chars=40)
    enviar = col_botao.form_submit_button("Pronunciar", type="primary", use_container_width=True)

if enviar:
    if not palavra.strip():
        st.warning("Digite uma palavra.")
    else:
        with st.spinner("Consultando o tutor..."):
            try:
                guardar_cartao(agente.pronunciar(palavra))
            except Exception as e:
                st.session_state.cartao = {"erro": f"Erro ao consultar o modelo: {e}"}
        st.rerun()

if st.session_state.cartao:
    mostrar_cartao(st.session_state.cartao)

# ---------- Chat ----------
st.markdown(
    '<div class="secao">💬 Tire suas dúvidas</div>'
    '<p class="ajuda">Depois de pesquisar uma palavra, pergunte aqui o que quiser sobre ela. Por exemplo:</p>'
    '<div class="sugestoes"><span>Quais palavras rimam com ela?</span><span>Quantas sílabas ela tem?</span>'
    '<span>Me dá outra frase de exemplo</span><span>Qual a diferença para “though”?</span></div>',
    unsafe_allow_html=True,
)
for msg in st.session_state.chat:
    with st.chat_message(msg["role"], avatar=AVATAR_ALUNO if msg["role"] == "user" else AVATAR_PROFESSOR):
        st.markdown(msg["content"])

if pergunta := st.chat_input("Escreva sua pergunta sobre a palavra pesquisada..."):
    st.session_state.chat.append({"role": "user", "content": pergunta})
    with st.chat_message("user", avatar=AVATAR_ALUNO):
        st.markdown(pergunta)
    with st.chat_message("assistant", avatar=AVATAR_PROFESSOR):
        with st.spinner("Pensando..."):
            try:
                resposta = agente.conversar(pergunta)
            except Exception as e:
                resposta = f"Erro ao consultar o modelo: {e}"
        st.markdown(resposta)
    st.session_state.chat.append({"role": "assistant", "content": resposta})
