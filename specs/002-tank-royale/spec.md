# Feature 002 — Batalha real de referência

**Origem:** S04-T02. **Estado inicial:** experimento autorizado; aceites globais S03/S04 continuam pendentes.

## US1 — Provar integração com o motor oficial

Como responsável, quero executar dois robôs oficiais sem GUI e obter resultados do motor, para verificar a viabilidade antes de desenvolver a competição.

Aceite: Walls e SpinBot oficiais; Tank Royale 1.4.0 e artefatos com SHA-256 fixados; cinco rounds Classic concluídos; pontuação/nomes copiados de BattleResults; replay oficial gzip legível. Duas execuções independentes devem passar, sem exigir vencedor ou placar idênticos. Logs simulados não contam.

## US2 — Não interferir no computador pessoal

Aceite: execução em contêiner descartável, sem rede externa, sem portas publicadas, sem volumes ou pastas do host montados, sem socket Docker, usuário não root e limites de CPU/memória/PIDs. O controlador local usa Docker para criar/remover somente o contêiner de nome aleatório desta invocação. O banco da plataforma não é utilizado. Download somente ao construir a imagem; runtime offline.

## US3 — Evidência e falha explícita

Aceite: comando único salva results.json, replay, engine.log e manifest.json em .local/tank-royale/<execucao>; valida artefatos e política efetiva via docker inspect; timeout retorna erro, nunca inventa resultado. Distinguir execução GitHub-hosted de execução no Windows do responsável.

## Exclusões

Não recebe código de alunos, não escolhe linguagem/autoria móvel definitiva, não implementa ranking do torneio, não abre acesso externo, não modifica Compose/banco/credenciais existentes. Restrições Docker são medidas do experimento, não prova de sandbox seguro para código hostil.
