# D-004 — Recorte do MVP e prioridade de segurança

**Data:** 2026-10-10. **Estado:** decisão de produto confirmada pelo responsável; não é homologação de sandbox ou arquitetura.

## Decisão confirmada

O MVP implementará somente a **RoboDSL básica**, com eventos, condições, ações e repetição controlada, em interface responsiva para programação, treino e participação. A versão 0.1 é a referência experimental, sujeita a correções essenciais, não a expansão ilimitada.

Recursos intermediários (variáveis, funções mais elaboradas, possível editor por blocos) e avançados (Java, Python ou outras linguagens gerais) serão **features futuras pós-MVP**. Não são pré-requisitos nem trabalho de implementação das sprints atuais.

## Prioridade confirmada

Antes de ampliar expressividade ou número de usuários, estabilizar a jornada básica e **resolver segurança, integridade de execução, proteção de dados e recuperação**. A RoboDSL continua entrada não confiável; código livre permanece negado. Não autorizar acesso de alunos apenas com base nos testes atuais de laboratório.

## O que não foi aprovado

Esta decisão não aprova automaticamente VM Linux, separação bot/árbitro, quotas, retenção de dados, infraestrutura pública ou testes de abuso no computador pessoal. Permanecem os gates D2–D5 e as aprovações das sprints S00/S03/S04/S08.

## Consequência no Spec Kit

Na feature 004, tratar D1 como decidido **quanto ao recorte inicial da linguagem**, ainda sujeito ao aceite pedagógico e à especificação funcional. Priorizar análise/provas de segurança com dados sintéticos em ambiente descartável; nenhuma VM foi instalada e nenhuma política foi aplicada ao host.

**Origem:** orientação expressa do responsável na conversa de 2026-10-10.