"""Ilustrações em SVG da interface: bandeiras, avatares e o fundo de sala de aula."""

import base64

# Bandeiras em SVG: os emojis de bandeira não aparecem no Windows (viram "BR" e "GB").
BANDEIRA_BR = (
    '<svg viewBox="0 0 28 20" preserveAspectRatio="xMidYMid slice">'
    '<clipPath id="br-c"><circle cx="14" cy="10" r="4.6"/></clipPath>'
    '<rect width="28" height="20" fill="#009C3B"/>'
    '<path d="M14 2.2 25.6 10 14 17.8 2.4 10z" fill="#FFDF00"/>'
    '<circle cx="14" cy="10" r="4.6" fill="#002776"/>'
    '<path d="M8.8 8.6Q14 7.4 19.2 11.4" stroke="#fff" stroke-width="1" fill="none" clip-path="url(#br-c)"/>'
    "</svg>"
)
BANDEIRA_UK = (
    '<svg viewBox="0 0 60 30" preserveAspectRatio="xMidYMid slice">'
    '<clipPath id="uk-s"><path d="M0,0 v30 h60 v-30 z"/></clipPath>'
    '<clipPath id="uk-t"><path d="M30,15 h30 v15 z v15 h-30 z h-30 v-15 z v-15 h30 z"/></clipPath>'
    '<g clip-path="url(#uk-s)">'
    '<path d="M0,0 v30 h60 v-30 z" fill="#012169"/>'
    '<path d="M0,0 L60,30 M60,0 L0,30" stroke="#fff" stroke-width="6"/>'
    '<path d="M0,0 L60,30 M60,0 L0,30" clip-path="url(#uk-t)" stroke="#C8102E" stroke-width="4"/>'
    '<path d="M30,0 v30 M0,15 h60" stroke="#fff" stroke-width="10"/>'
    '<path d="M30,0 v30 M0,15 h60" stroke="#C8102E" stroke-width="6"/>'
    "</g></svg>"
)

# Aluno: camiseta verde e amarela, capelo de formatura e mochila.
AVATAR_ALUNO = (
    '<svg viewBox="0 0 64 64">'
    '<circle cx="32" cy="32" r="32" fill="#DFF5E7"/>'
    '<path d="M10 64c2-12 10-18 22-18s20 6 22 18z" fill="#009C3B"/>'
    '<path d="M24 47l8 7 8-7" fill="#FFDF00"/>'
    '<rect x="13" y="50" width="6" height="14" rx="2" fill="#012169"/>'
    '<rect x="28" y="38" width="8" height="9" fill="#F2C29B"/>'
    '<circle cx="32" cy="29" r="12" fill="#F6CBA3"/>'
    '<path d="M20 28c0-8 5-12 12-12s12 4 12 12c-2-4-6-6-12-6s-10 2-12 6z" fill="#5A3A22"/>'
    '<path d="M16 17l16-7 16 7-16 7z" fill="#0F1B2D"/>'
    '<rect x="25" y="19" width="14" height="5" fill="#0F1B2D"/>'
    '<path d="M46 17.5v9" stroke="#FFDF00" stroke-width="1.6"/><circle cx="46" cy="27.5" r="1.8" fill="#FFDF00"/>'
    '<circle cx="27.5" cy="30" r="1.6" fill="#0F1B2D"/><circle cx="36.5" cy="30" r="1.6" fill="#0F1B2D"/>'
    '<path d="M28 35q4 3.2 8 0" stroke="#0F1B2D" stroke-width="1.6" fill="none" stroke-linecap="round"/>'
    '<circle cx="24.5" cy="33.5" r="1.8" fill="#F29C8C" opacity=".6"/>'
    '<circle cx="39.5" cy="33.5" r="1.8" fill="#F29C8C" opacity=".6"/>'
    "</svg>"
)

# Professor: blazer azul-marinho, gravata vermelha, óculos e um livro de inglês.
AVATAR_PROFESSOR = (
    '<svg viewBox="0 0 64 64">'
    '<circle cx="32" cy="32" r="32" fill="#E3E9FA"/>'
    '<path d="M10 64c2-12 10-18 22-18s20 6 22 18z" fill="#012169"/>'
    '<path d="M26 46l6 8 6-8z" fill="#FFFFFF"/>'
    '<path d="M30.5 49h3l1 9-2.5 3-2.5-3z" fill="#C8102E"/>'
    '<rect x="28" y="38" width="8" height="9" fill="#D9A47E"/>'
    '<circle cx="32" cy="29" r="12" fill="#E3B48F"/>'
    '<path d="M19.5 29c-1-10 4-15 12.5-15s13.5 5 12.5 15c-1-5-3-7-5-8-4 2-11 2-16 0-2 1-3 4-4 8z" fill="#8A8F99"/>'
    '<circle cx="27" cy="30" r="4" fill="none" stroke="#0F1B2D" stroke-width="1.6"/>'
    '<circle cx="37" cy="30" r="4" fill="none" stroke="#0F1B2D" stroke-width="1.6"/>'
    '<path d="M31 30h2" stroke="#0F1B2D" stroke-width="1.6"/>'
    '<circle cx="27" cy="30" r="1.3" fill="#0F1B2D"/><circle cx="37" cy="30" r="1.3" fill="#0F1B2D"/>'
    '<path d="M28 36q4 2.6 8 0" stroke="#0F1B2D" stroke-width="1.6" fill="none" stroke-linecap="round"/>'
    '<rect x="41" y="50" width="14" height="11" rx="1.5" fill="#C8102E" transform="rotate(-10 48 55)"/>'
    '<text x="48" y="58" font-size="6" font-weight="700" fill="#fff" text-anchor="middle" '
    'font-family="Arial, sans-serif" transform="rotate(-10 48 55)">ABC</text>'
    "</svg>"
)

# Ícones de traço (estilo Lucide), coloridos pela cor do texto ao redor.
ICONES = {
    "ouvir": '<path d="M11 5 6 9H2v6h4l5 4V5z"/><path d="M15.5 8.5a5 5 0 0 1 0 7"/><path d="M19 5a10 10 0 0 1 0 14"/>',
    "busca": '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>',
    "dica": (
        '<path d="M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A6 6 0 0 0 6 8c0 1 .2 2.2 1.5 3.5.7.7 1.3 1.5 1.5 2.5"/>'
        '<path d="M9 18h6"/><path d="M10 22h4"/>'
    ),
    "livro": '<path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>',
    "chat": '<path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z"/>',
    "brilho": (
        '<path d="m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 '
        '1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3Z"/>'
    ),
    "troca": '<path d="M8 3 4 7l4 4"/><path d="M4 7h16"/><path d="m16 21 4-4-4-4"/><path d="M20 17H4"/>',
    "restaurar": '<path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/>',
    "aspas": '<path d="M7 7h4v4c0 3-2 5-4 5"/><path d="M15 7h4v4c0 3-2 5-4 5"/>',
    "microfone": (
        '<path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/>'
        '<path d="M19 10v2a7 7 0 0 1-14 0v-2"/><path d="M12 19v3"/>'
    ),
}


def icone(nome: str, tamanho: int = 18) -> str:
    return (
        f'<svg class="icone" width="{tamanho}" height="{tamanho}" viewBox="0 0 24 24" fill="none" '
        'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" '
        f'aria-hidden="true">{ICONES[nome]}</svg>'
    )


_CORES_SALA = {
    "claro": {
        "parede": "#EAF2EC", "lambri": "#D8E7DD", "piso": "#E4CDAA", "tabua": "#D3B78F",
        "madeira": "#A9744F", "lousa": "#2F5D46", "giz": "#F4F7F2", "papel": "#FFFFFF",
        "linha": "#C3D3C8", "texto": "#33475B", "opacidade": "1",
    },
    "escuro": {
        "parede": "#14213A", "lambri": "#101B31", "piso": "#1B2438", "tabua": "#232E47",
        "madeira": "#5B4030", "lousa": "#173426", "giz": "#D5E0D8", "papel": "#1F2B45",
        "linha": "#2B3A5A", "texto": "#9FB0C8", "opacidade": ".8",
    },
}


def _sala_svg(c: dict) -> str:
    partes = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 900" preserveAspectRatio="xMidYMax slice">',
        f'<rect width="1600" height="900" fill="{c["parede"]}"/>',
        f'<rect y="630" width="1600" height="130" fill="{c["lambri"]}"/>',
        f'<rect y="626" width="1600" height="8" fill="{c["madeira"]}"/>',
        f'<rect y="760" width="1600" height="140" fill="{c["piso"]}"/>',
        f'<g opacity="{c["opacidade"]}">',
    ]
    # Tábuas do piso
    for x in range(0, 1600, 160):
        partes.append(f'<path d="M{x} 760v140" stroke="{c["tabua"]}" stroke-width="3"/>')
    partes.append(f'<path d="M0 830h1600" stroke="{c["tabua"]}" stroke-width="3"/>')

    # Bandeirinhas nas cores do Brasil e do Reino Unido
    cores = ["#009C3B", "#FFDF00", "#012169", "#C8102E"]
    partes.append(f'<path d="M0 30 Q800 110 1600 30" stroke="{c["texto"]}" stroke-width="2" fill="none"/>')
    for i, x in enumerate(range(20, 1600, 70)):
        t = x / 1600
        y = (1 - t) ** 2 * 30 + 2 * (1 - t) * t * 110 + t**2 * 30
        partes.append(f'<path d="M{x - 20} {y:.0f}h40l-20 36z" fill="{cores[i % 4]}"/>')

    # Alfabeto acima da lousa
    for i, letra in enumerate("ABCDEFGHIJ"):
        x = 430 + i * 75
        partes.append(
            f'<rect x="{x}" y="105" width="62" height="44" rx="6" fill="{c["papel"]}" stroke="{c["linha"]}"/>'
            f'<text x="{x + 31}" y="137" font-size="24" font-weight="700" text-anchor="middle" '
            f'font-family="Arial, sans-serif" fill="{cores[i % 4]}">{letra}{letra.lower()}</text>'
        )

    # Lousa com frases em giz
    giz = f'fill="{c["giz"]}" font-family="Segoe Print, Comic Sans MS, Chalkboard SE, cursive"'
    partes += [
        f'<rect x="390" y="170" width="820" height="370" rx="10" fill="{c["madeira"]}"/>',
        f'<rect x="408" y="188" width="784" height="334" rx="4" fill="{c["lousa"]}"/>',
        f'<text x="450" y="260" font-size="50" {giz}>Hello!  =  Olá!</text>',
        f'<text x="450" y="340" font-size="40" {giz}>think → /θɪŋk/</text>',
        f'<text x="450" y="410" font-size="40" {giz}>How do you say...?</text>',
        f'<path d="M450 435 q60 14 120 0 t120 0" stroke="{c["giz"]}" stroke-width="3" fill="none"/>',
        f'<circle cx="1130" cy="478" r="22" stroke="{c["giz"]}" stroke-width="3" fill="none"/>',
        f'<path d="M1121 472v2M1139 472v2M1119 484q11 10 22 0" stroke="{c["giz"]}" stroke-width="3" fill="none" stroke-linecap="round"/>',
        f'<rect x="380" y="540" width="840" height="14" rx="4" fill="{c["madeira"]}"/>',
        '<rect x="520" y="531" width="28" height="9" rx="3" fill="#FFFFFF"/>',
        '<rect x="560" y="531" width="22" height="9" rx="3" fill="#FFDF00"/>',
        '<rect x="1040" y="526" width="60" height="14" rx="3" fill="#4B5563"/>',
    ]

    # Relógio
    partes += [
        f'<circle cx="200" cy="250" r="68" fill="{c["papel"]}" stroke="{c["madeira"]}" stroke-width="10"/>',
        f'<path d="M200 250V205M200 250l32 18" stroke="{c["texto"]}" stroke-width="6" stroke-linecap="round"/>',
        '<circle cx="200" cy="250" r="6" fill="#C8102E"/>',
    ]
    for i in range(12):
        partes.append(
            f'<rect x="197" y="190" width="6" height="12" fill="{c["texto"]}" transform="rotate({i * 30} 200 250)"/>'
        )

    # Pôster do Big Ben
    partes += [
        f'<rect x="120" y="360" width="160" height="220" rx="8" fill="{c["papel"]}" stroke="{c["linha"]}" stroke-width="3"/>',
        '<rect x="135" y="375" width="130" height="160" fill="#BFD7F5"/>',
        '<path d="M182 535V430h36v105z" fill="#8C6A3F"/>',
        '<path d="M178 430h44l-22-45z" fill="#5E4526"/>',
        '<circle cx="200" cy="450" r="12" fill="#FFF3C4" stroke="#5E4526" stroke-width="2"/>',
        '<path d="M190 480h20M190 500h20M190 520h20" stroke="#5E4526" stroke-width="2"/>',
        f'<text x="200" y="563" font-size="18" font-weight="700" text-anchor="middle" '
        f'font-family="Arial, sans-serif" fill="{c["texto"]}">LONDON</text>',
    ]

    # Bandeiras emolduradas
    partes += [
        f'<rect x="1290" y="180" width="180" height="100" rx="6" fill="{c["madeira"]}"/>',
        f'<svg x="1300" y="190" width="160" height="80" viewBox="0 0 60 30" preserveAspectRatio="none">{BANDEIRA_UK[BANDEIRA_UK.index(">") + 1:]}',
        f'<rect x="1290" y="300" width="180" height="128" rx="6" fill="{c["madeira"]}"/>',
        f'<svg x="1300" y="310" width="160" height="108" viewBox="0 0 28 20" preserveAspectRatio="none">{BANDEIRA_BR[BANDEIRA_BR.index(">") + 1:]}',
    ]

    # Estante com livros
    partes += [
        f'<rect x="1270" y="450" width="230" height="300" fill="{c["madeira"]}"/>',
        f'<rect x="1282" y="462" width="206" height="276" fill="{c["lambri"]}"/>',
        f'<rect x="1282" y="592" width="206" height="10" fill="{c["madeira"]}"/>',
    ]
    livros = ["#C8102E", "#012169", "#009C3B", "#F5C400", "#7C3AED", "#0EA5E9", "#C8102E", "#009C3B"]
    for prateleira, base in enumerate((592, 738)):
        x = 1292
        for i, cor in enumerate(livros):
            larg, alt = 20 + (i * 7) % 9, 90 + (i * 13 + prateleira * 5) % 30
            partes.append(f'<rect x="{x}" y="{base - alt}" width="{larg}" height="{alt}" rx="2" fill="{cor}"/>')
            x += larg + 3

    # Mesa do professor com globo e maçã
    partes += [
        f'<rect x="90" y="660" width="360" height="22" rx="4" fill="{c["madeira"]}"/>',
        f'<rect x="110" y="682" width="20" height="120" fill="{c["madeira"]}"/>',
        f'<rect x="410" y="682" width="20" height="120" fill="{c["madeira"]}"/>',
        f'<rect x="300" y="682" width="110" height="70" fill="{c["madeira"]}" opacity=".85"/>',
        '<path d="M190 660v-20" stroke="#5E4526" stroke-width="6"/>',
        '<ellipse cx="190" cy="660" rx="30" ry="6" fill="#5E4526"/>',
        '<circle cx="190" cy="595" r="45" fill="#3B82F6"/>',
        '<path d="M160 575q15-15 30-5t15 25-20 15-25-35zM205 610q15 0 20 12-15 10-25 0z" fill="#22A35A"/>',
        f'<path d="M190 548a47 47 0 0 1 0 94" stroke="{c["texto"]}" stroke-width="4" fill="none"/>',
        '<circle cx="330" cy="645" r="16" fill="#E11D48"/><path d="M330 630q2-8 8-10" stroke="#5E4526" stroke-width="3" fill="none"/>',
        '<rect x="250" y="640" width="50" height="20" rx="2" fill="#012169"/>',
        '<rect x="254" y="628" width="44" height="14" rx="2" fill="#F5C400"/>',
    ]

    # Carteiras dos alunos
    for x in (620, 900):
        partes += [
            f'<rect x="{x}" y="740" width="170" height="16" rx="4" fill="{c["madeira"]}"/>',
            f'<rect x="{x + 12}" y="756" width="12" height="90" fill="{c["madeira"]}"/>',
            f'<rect x="{x + 146}" y="756" width="12" height="90" fill="{c["madeira"]}"/>',
            f'<rect x="{x + 50}" y="728" width="60" height="12" rx="2" fill="{c["papel"]}" stroke="{c["linha"]}"/>',
        ]

    # Planta no canto
    partes += [
        '<path d="M1540 760l-12-60h64l-12 60z" fill="#B45309"/>',
        '<path d="M1560 700q-40-50-10-110q10 60 10 110zM1560 700q30-60 70-80q-20 50-70 80zM1560 700q-50-20-70-70q50 10 70 70z" fill="#22A35A"/>',
        "</g></svg>",
    ]
    return "".join(partes)


def fundo_sala(tema: str) -> str:
    """URL (data URI) do fundo de sala de aula nas cores do tema."""
    svg = _sala_svg(_CORES_SALA[tema])
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()
