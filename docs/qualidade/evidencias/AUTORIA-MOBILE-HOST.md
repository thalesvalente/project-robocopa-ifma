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
- O **Explorador foi posteriormente demonstrado no PC** em segunda captura, com programa e métricas diferentes; não houve inspeção independente dos arquivos nem teste de edição livre de um terceiro programa.
- Não houve teste em smartphone físico (toque, teclado virtual, rede, ergonomia).
- Não houve acesso LAN/remoto, inscrições de estudantes, isolamento aprovado para código não confiável nem aprovação pedagógica da linguagem candidata.

## Estado e próximos aceites

## Segunda captura — Explorador

Uma nova captura de tela compartilhada pelo responsável mostra o exemplo **Explorador** carregado e o painel após a execução de três rounds no computador hospedeiro:

- Bloco `sempre`: `velocidade 6`, `girar 8`, `canhao 20`.
- Bloco `ao detectar`: `se energia > 20`, `atirar 2`, alternativa `atirar 1`.
- Painel do motor: **Walls em primeiro com 188 pontos; Aprendiz em segundo com 188 pontos**.
- Indicadores do Aprendiz: **velocidade média absoluta 5,47** e **94,3% dos turnos observados em movimento**.
- Replay apresentado no **round 3, turno 748, amostra 289/289**.
- Interface informa conclusão da batalha e exibe identificador de versão do programa.

### Comparação de comportamento local

| Exemplo | Aprendiz | Walls | Velocidade média absoluta do Aprendiz | Turnos em movimento |
|---|---:|---:|---:|---:|
| Sentinela | 536 | 226 | 0,00 | 0,0% |
| Explorador | 188 | 188 | 5,47 | 94,3% |

As duas capturas são resultados de **execuções separadas**, sujeitos a condições dinâmicas do motor. O contraste de movimento é coerente com os códigos exibidos. Os placares não permitem concluir superioridade estatística de qualquer estratégia.

**Ponto aberto de regra/classificação:** na segunda captura há empate no total de pontos exibidos (188 × 188), mas a interface mostra posições 1º e 2º. É necessário verificar a política efetiva de ranking/desempate do motor e definir regras explícitas da competição na S03-T03. Não presumir erro nem desempate correto sem examinar resultado estruturado e implementação.

## Estado e próximos aceites

MOB-008 parcialmente atendida: **ambos os exemplos, os dois treinamentos e o replay foram observados no PC por capturas**. Permanecem pendentes teste em smartphone físico, inspeção independente de `results.json`/`manifest.json`/`*.battle.gz` das execuções locais e avaliação pedagógica da autoria. MOB-009 segue pendente. A tarefa macro S04-T03 permanece em revisão/preparação, sem ratificação de S03/S04.

As imagens compartilhadas **não foram incluídas no repositório público**; somente os resultados técnicos necessários foram descritos.

**Próximos testes recomendados:** conferir o comportamento ao modificar uma condição por conta própria, reproduzir em telefone físico através de acesso controlado sem expor o servidor de laboratório (ele tem acesso à CLI Docker) e esclarecer a ordenação do empate no sistema de classificação.
