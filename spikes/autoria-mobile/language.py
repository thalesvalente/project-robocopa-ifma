"""RoboDSL 0.1: bounded event/condition language; never evals participant text.

Only numeric literals validated here enter the fixed Java template. Comments,
identifiers, strings, imports, expressions and paths are never emitted from input.
This educational experiment is not a production sandbox for hostile programs.
"""
from __future__ import annotations
import hashlib
import json
import re
import unicodedata

VERSION = '0.1'
MAX_BYTES = 8192
MAX_LINES = 160
MAX_NODES = 80
MAX_DEPTH = 3
EVENTS = {'sempre': 'tick', 'ao detectar': 'scan'}
ACTIONS = {
    'velocidade': ('setTargetSpeed', -8, 8),
    'girar': ('setTurnRate', -10, 10),
    'canhao': ('setGunTurnRate', -20, 20),
    'atirar': ('setFire', 0.1, 3),
}
NUMBER = r'-?(?:0|[1-9][0-9]{0,3})(?:\.[0-9]{1,3})?'
ACTION_RE = re.compile(r'(velocidade|girar|canhao|atirar) (' + NUMBER + r')')
IF_RE = re.compile(r'se (energia|distancia) (<=|>=|==|<|>) (' + NUMBER + r')')
EXAMPLES = {
    'sentinela': 'sempre\n  velocidade 0\n  girar 0\n  canhao 20\nfim\n\nao detectar\n  se distancia < 250\n    atirar 3\n  senao\n    atirar 1\n  fim\nfim\n',
    'explorador': 'sempre\n  velocidade 6\n  girar 8\n  canhao 20\nfim\n\nao detectar\n  se energia > 20\n    atirar 2\n  senao\n    atirar 1\n  fim\nfim\n',
}

class ProgramError(ValueError):
    def __init__(self, line: int, message: str):
        super().__init__(f'Linha {line}: {message}')
        self.line, self.message = line, message


def parse(source: str) -> dict:
    if not isinstance(source, str):
        raise ProgramError(1, 'Envie o programa como texto.')
    if len(source.encode('utf-8')) > MAX_BYTES or len(source.splitlines()) > MAX_LINES:
        raise ProgramError(1, 'Programa muito grande: limite de 8 KiB e 160 linhas.')
    lines = []
    for number, raw in enumerate(source.splitlines(), 1):
        text = ' '.join(raw.split('#', 1)[0].strip().lower().split())
        text = ''.join(c for c in unicodedata.normalize('NFD', text) if not unicodedata.combining(c))
        if text:
            lines.append((number, text))
    position, nodes = 0, 0

    def block(event: str, depth: int) -> list:
        nonlocal position, nodes
        if depth > MAX_DEPTH:
            raise ProgramError(lines[position][0] if position < len(lines) else 1,
                               'Use no máximo três níveis de condições.')
        statements = []
        while position < len(lines):
            number, text = lines[position]
            if text in ('fim', 'senao'):
                break
            position += 1
            nodes += 1
            if nodes > MAX_NODES:
                raise ProgramError(number, 'Use no máximo 80 instruções e condições.')
            action = ACTION_RE.fullmatch(text)
            condition = IF_RE.fullmatch(text)
            if action:
                name, literal = action.groups()
                value = float(literal)
                _, low, high = ACTIONS[name]
                if not low <= value <= high:
                    raise ProgramError(number, f'{name}: o valor deve ficar entre {low} e {high}.')
                statements.append({'op': name, 'value': value})
            elif condition:
                sensor, operator, literal = condition.groups()
                value = float(literal)
                if sensor == 'distancia' and event != 'scan':
                    raise ProgramError(number, 'distancia só existe dentro de "ao detectar".')
                if not 0 <= value <= 2000:
                    raise ProgramError(number, 'O limite da condição deve ficar entre 0 e 2000.')
                yes = block(event, depth + 1)
                no = []
                if position < len(lines) and lines[position][1] == 'senao':
                    position += 1
                    no = block(event, depth + 1)
                if position >= len(lines) or lines[position][1] != 'fim':
                    raise ProgramError(number, 'Feche esta condição com "fim".')
                position += 1
                if not yes:
                    raise ProgramError(number, 'Escreva ao menos uma ação depois de "se".')
                statements.append({'op': 'if', 'sensor': sensor, 'operator': operator,
                                   'value': value, 'yes': yes, 'no': no})
            else:
                raise ProgramError(number, 'Instrução desconhecida. Use a referência abaixo do editor.')
        return statements

    result = {}
    while position < len(lines):
        number, text = lines[position]
        if text not in EVENTS:
            raise ProgramError(number, 'Comece um bloco com "sempre" ou "ao detectar".')
        event = EVENTS[text]
        if event in result:
            raise ProgramError(number, 'Este evento já foi definido. Junte suas instruções no mesmo bloco.')
        position += 1
        result[event] = block(event, 0)
        if position >= len(lines) or lines[position][1] != 'fim':
            raise ProgramError(number, 'Feche o bloco de evento com "fim".')
        if not result[event]:
            raise ProgramError(number, 'O bloco precisa de ao menos uma instrução.')
        position += 1
    if set(result) != {'tick', 'scan'}:
        raise ProgramError(1, 'O programa deve conter "sempre" e "ao detectar", ambos fechados com "fim".')
    return {'version': VERSION, 'events': result, 'node_count': nodes}


def compile_program(source: str) -> dict:
    ast = parse(source)
    canonical = json.dumps(ast, sort_keys=True, separators=(',', ':'), ensure_ascii=True)
    code_hash = hashlib.sha256(canonical.encode()).hexdigest()

    def emit(statements: list, indent: int) -> str:
        output = []
        pad = ' ' * indent
        for node in statements:
            literal = format(node['value'], '.12g')
            if node['op'] == 'if':
                sensor = 'getEnergy()' if node['sensor'] == 'energia' else 'distanceTo(e.getX(), e.getY())'
                output.append(f"{pad}if ({sensor} {node['operator']} {literal}) {{")
                output.append(emit(node['yes'], indent + 4))
                if node['no']:
                    output.append(pad + '} else {')
                    output.append(emit(node['no'], indent + 4))
                output.append(pad + '}')
            else:
                method = ACTIONS[node['op']][0]
                output.append(f'{pad}{method}({literal});')
        return '\n'.join(output)

    java = '''import dev.robocode.tankroyale.botapi.Bot;
import dev.robocode.tankroyale.botapi.events.ScannedBotEvent;
public class Aprendiz extends Bot {
    public static void main(String[] args) { new Aprendiz().start(); }
    @Override public void run() {
        while (isRunning()) {
%s
            go();
        }
    }
    @Override public void onScannedBot(ScannedBotEvent e) {
%s
    }
}
''' % (emit(ast['events']['tick'], 12), emit(ast['events']['scan'], 8))
    return {'ast': ast, 'program_sha256': code_hash, 'java': java,
            'java_sha256': hashlib.sha256(java.encode()).hexdigest()}
