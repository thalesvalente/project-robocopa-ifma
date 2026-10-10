# Evidência — interface e treino observados no computador hospedeiro

**Data do relato:** 2026-10-09 (horário local).  
**Origem:** captura de tela e confirmação do responsável na conversa, após as instruções de execução do laboratório S04-T03.  
**Classificação:** observação visual de funcionamento no PC; não equivale a revisão independente dos arquivos produzidos pela execução.

## O que a captura demonstra

- Interface do experimento de autoria carregada, com título "O próximo movimento é seu", editor RoboDSL e painel de resultados/replay.
- Exemplo **Sentinela** visível no editor: bloco `sempre` com `velocidade 0`, `girar 0`, `canhao 20`; bloco `ao detectar` com condição de distância para a potência do disparo.
- O painel exibe **"Resultado do motor · 3 rounds"**, com **Aprendiz em primeiro: 536 pontos** e **Walls em segundo: 226 pontos**.
- Indicadores do Aprendiz: **velocidade média absoluta 0,00** e **0,0% dos turnos observados em movimento**, coerentes com a estratégia Sentinela.
- O replay visual está no **round 3, turno 707, amostra 292/292**, com robôs desenhados na arena.
- Mensagem inferior visível informa **"Batalha concluída. Compare o replay e altere sua estratégia."**
- Responsável confirmou no chat que o experimento funcionou.

## O que NÃO foi verificado

- A captura não foi publicada no repositório público; somente seus dados técnicos não identificáveis foram resumidos.
- Não foram anexados ou inspecionados os arquivos locais `results.json`, `manifest.json` e `*.battle.gz` dessa execução. Os placares são os **exibidos na UI**, não uma auditoria independente do replay.
- Não foi demonstrada a execução do **Explorador** no PC nem a alteração de código pelo responsável e nova medição nessa mesma sessão.
- Não houve teste em smartphone físico (toque, teclado virtual, rede, ergonomia).
- Não houve acesso LAN/remoto, inscrições de estudantes, isolamento aprovado para código não confiável nem aprovação pedagógica da linguagem candidata.

## Estado e próximos aceites

MOB-008 parcialmente atendida: **interface e treino observados no PC**, pendente teste físico e conferência opcional dos artefatos locais. MOB-009 segue pendente. A tarefa macro S04-T03 permanece em revisão/preparação, sem ratificação de S03/S04.

**Próximo teste recomendado:** no próprio PC, carregar `Exemplo: explorador`, executar novamente, observar movimento efetivo e comparar métricas. Em seguida, preparar forma *controlada e autorizada* de acesso a um telefone físico, sem simplesmente publicar a porta do servidor local que tem acesso à CLI Docker.
