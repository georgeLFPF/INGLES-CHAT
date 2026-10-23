"""Memória de curto prazo: últimas mensagens e palavras estudadas na sessão."""

from collections import deque


class MemoriaCurtoPrazo:
    def __init__(self, max_mensagens: int = 12, max_palavras: int = 20):
        self.mensagens: deque[dict] = deque(maxlen=max_mensagens)
        self.palavras: deque[str] = deque(maxlen=max_palavras)

    def adicionar(self, role: str, content: str) -> None:
        self.mensagens.append({"role": role, "content": content})

    def registrar_palavra(self, palavra: str) -> None:
        palavra = palavra.strip().lower()
        if palavra in self.palavras:
            self.palavras.remove(palavra)
        self.palavras.append(palavra)

    def historico(self) -> list[dict]:
        return list(self.mensagens)

    def contexto(self) -> str:
        """Resumo curto para o prompt de sistema (resolve 'ela', 'essa palavra', etc.)."""
        if not self.palavras:
            return "Nenhuma palavra estudada ainda nesta sessão."
        return (
            "Palavras estudadas nesta sessão (a última é a mais recente): "
            + ", ".join(self.palavras)
        )

    def limpar(self) -> None:
        self.mensagens.clear()
        self.palavras.clear()
