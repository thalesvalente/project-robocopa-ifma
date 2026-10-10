# Governança, responsabilidades e riscos

**Versão:** 0.1.0 · **Data:** 2026-10-09 · **Tarefa:** S02-T04.
**Estado:** minuta de organização; pessoas, vínculos e aprovações institucionais ainda não designados, salvo o responsável que conduz o projeto nesta conversa.

## Responsabilidades por papel

| Papel | Responsabilidade | Não confundir com |
|---|---|---|
| Responsável pelo projeto/produto | Priorizar escopo, revisar entregas, autorizar liberação e assumir decisões de operação | Aceite automático de qualquer conteúdo gerado |
| Professor mediador | Adequar atividade, orientar e avaliar a aprendizagem | Operador obrigatório da infraestrutura |
| Organizador da competição | Aplicar regulamento, tratar inscrições e incidentes e conferir resultados | Permissão para alterar placar sem registro |
| Operador do host | Configuração autorizada, serviços, limites, backup e recuperação | Acesso indiscriminado a dados pessoais de participantes |
| Executor de desenvolvimento | Implementação, testes, documentação e evidências conforme tarefa | Autoridade institucional ou homologação pedagógica |
| Revisor institucional a definir | Avaliar enquadramento, participação e tratamento de dados quando necessário | Parceiro já confirmado |

Uma pessoa pode acumular papéis no piloto; as responsabilidades e permissões continuam distintas. ChatGPT e Codex apoiam o trabalho, mas não assinam aprovações institucionais nem comprovam testes que não foram executados.

## Decisões e registros

Escopo, arquitetura, regulamento e liberação devem possuir responsável, motivo e evidência. Alterações de código usam branch, commit e PR. Requisitos e tarefas mantêm IDs. Incidentes e reexecuções seguem o regulamento, sem exclusão silenciosa de resultados desfavoráveis.

O responsável autorizou a execução do planejamento no repositório. Instalação persistente na máquina, exposição externa, configuração de DNS/firewall/túnel e recrutamento de participantes exigem contexto e autorização próprios.

## Riscos iniciais

| ID | Risco | Controle proposto | Verificação antes de liberar |
|---|---|---|---|
| R01 | Código de bot comprometer host ou dados | Executor segregado; limites; privilégio mínimo; negar acesso a arquivos e serviços internos | Modelo de ameaças e testes negativos S04/S08 |
| R02 | Saturação ou indisponibilidade da máquina | Limites de simultaneidade/fila; recursos reservados; janela operacional | Ensaio de carga e critério de parada |
| R03 | Perda de versões ou resultados | Persistência, backup e retenção definidos | Restauração real e recuperação de jobs |
| R04 | Autoria móvel frustrante ou inviável | Experimento comparativo; superfície de edição reduzida; mensagens recuperáveis | Observação em dispositivo real |
| R05 | Vantagem indevida por edição posterior | Versão inscrita imutável e regra de fechamento | Teste de edição após encerramento |
| R06 | Pontuação duplicada ou incorreta | Regras versionadas, idempotência e fixtures | Ensaio com falha, retry e desempate |
| R07 | Exposição de dados pessoais ou credenciais | Dados mínimos; exclusões no Git; acesso por papel; revisão de publicação | Inspeção de diff/logs e revisão responsável |
| R08 | Escopo crescer antes da prova de valor | Uma abordagem de autoria e um formato; controle de mudanças | Revisão de prioridade por sprint |
| R09 | Atividade não adequar-se ao nível de entrada | Revisão docente, exemplos e piloto pequeno | Observação e ajuste pedagógico |
| R10 | Dependência excessiva de uma pessoa | Runbooks, decisões e recuperação documentados | Outra pessoa autorizada consegue compreender a operação a partir dos guias |

Probabilidade e impacto numéricos não foram estimados por falta de dados. Segurança do host, integridade e recuperação são bloqueios de liberação, independentemente de interesse dos participantes.

## Tratamento inicial dos dados

Adotar convites e identificadores mínimos. Não publicar no repositório público nomes de alunos, contatos, imagens, gravações, credenciais, endereços residenciais ou cópias do banco. Estabelecer finalidade, acesso, retenção e exclusão antes do piloto. Participação de menores e enquadramento institucional devem passar pela revisão responsável aplicável; este documento não substitui análise jurídica ou institucional.

## Condições de parada

Suspender novas execuções diante de falha de isolamento, acesso indevido, corrupção de resultado, incapacidade de recuperação ou consumo que comprometa o host. Preservar evidência sanitizada, comunicar o responsável e aplicar correção/reteste antes de retomar. Não ocultar incidentes para manter o evento aparentando normalidade.
