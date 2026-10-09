# Entregas, recursos e custos operacionais

**Versão:** 0.1.0 · **Data:** 2026-10-09 · **Tarefa:** S02-T02.
**Estado:** estrutura preparatória. Não é cotação, orçamento aprovado ou medição de consumo/capacidade.

## Estrutura analítica das entregas

| Pacote | Entregas verificáveis | Sprints |
|---|---|---|
| 1. Governança e descoberta | Constituição, backlog, Spec Kit, problema, jornadas, BMC e hipóteses | S00–S01 |
| 2. Projeto e comunicação | Projeto, recursos, trilha pedagógica, responsabilidades e pitch | S02 |
| 3. Especificação | RF, RNF, regras, restrições, fluxos e critérios de aceite | S03 |
| 4. Viabilidade e arquitetura | Spikes de motor, autoria e isolamento; decisões, interfaces e plano técnico | S04 |
| 5. Jornada básica | Acesso, interface, projetos, versões e orientação | S05 |
| 6. Execução e competição | Editor, validação, executor, treino, inscrição, partidas e resultados | S06–S07 |
| 7. Operação e qualidade | Testes integrados, segurança, capacidade, implantação, restauração e rollback | S08 |
| 8. Validação e entrega | Piloto, correções, homologação, guias, pitch atualizado e release | S09 |

## Recursos e lacunas

A máquina do responsável é a infraestrutura definida para o MVP. As informações relatadas de Core i9 e 128 GB de RAM não permitem concluir quantidade de alunos ou batalhas simultâneas. Será preciso reservar recursos para o uso pessoal e verificar virtualização, armazenamento, temperatura, conectividade, disponibilidade e política de backup.

O piloto também depende de tempo para preparar atividades, orientar estudantes e operar a competição. Capacidade computacional não substitui capacidade de atendimento e mediação.

## Registro de custos

| Categoria | Como levantar | Estado |
|---|---|---|
| Energia incremental | Medir potência adicional durante a operação e horas de uso; aplicar tarifa efetiva informada pelo responsável | Não medido |
| Conectividade | Identificar eventual gasto adicional necessário ao piloto, sem presumir contratação nova | Não levantado |
| Armazenamento e backup | Estimar volume de versões, resultados e logs; definir retenção e cópia separada | Não dimensionado |
| Manutenção/depreciação | Registrar critério de alocação da máquina e reposições relacionadas ao projeto | Não estimado |
| Domínio e acesso externo | Somente após decisão de topologia e autorização; verificar necessidade real | Não decidido |
| Serviços e ferramentas | Separar uso já contratado de custos adicionais e limites de uso | Não levantado |
| Desenvolvimento, revisão e operação | Registrar esforço por atividade e papel; distinguir contribuição voluntária de contratação | Não estimado |
| Mediação pedagógica | Preparação, oficina, acompanhamento e avaliação | Não estimado |

Nenhuma célula desconhecida foi substituída por zero. Hospedar em equipamento existente pode evitar contratação imediata de servidor, mas não elimina consumo, tempo, risco de indisponibilidade e manutenção.

## Modelo de cálculo, sem valores presumidos

Energia incremental estimada em kWh = potência adicional média medida em watts ÷ 1.000 × horas de operação. Custo de energia = consumo incremental × tarifa efetiva aplicável informada pelo responsável. O cálculo deve distinguir potência nominal do equipamento e consumo realmente observado.

Custo operacional do piloto = desembolsos incrementais efetivos + custos alocados conforme critério explícito. Horas de dedicação podem ser apresentadas separadamente, sem inventar remuneração ou misturar contribuição com saída de caixa.

## Dimensionamento experimental

Como cenário inicial de ensaio, o plano admite avaliar 20 sessões, oito robôs inscritos e uma batalha por vez. Esses números são parâmetros propostos para teste, não capacidade demonstrada nem quantidade de participantes autorizada. O piloto será dimensionado pelos resultados, com limites claros de fila e execução.

Separar três medidas: tempo de resposta da interface/API, espera na fila e duração da batalha. Não apresentar a soma como se fosse apenas latência da rede ou desempenho do celular.

## Próximas evidências necessárias

Inventário verificado no host; decisão de ambiente segregado; medição de recursos no spike; definição de retenção; ensaio com carga; estimativa de esforço de mediação; critérios de disponibilidade. Nenhuma contratação, abertura de porta ou alteração da máquina decorre automaticamente deste documento.
