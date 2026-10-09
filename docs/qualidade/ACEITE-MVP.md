# Critérios propostos de aceite do MVP

**Estado:** proposta, a detalhar na S03 e homologar na S09. Nenhum resultado do produto foi executado nesta fundação.

| ID | Obrigação | Evidência esperada |
|---|---|---|
| AC-01 | Acesso com papéis corretos e dados mínimos | Testes positivos e negativos de autorização |
| AC-02 | Criar e alterar lógica pelo celular | Roteiro E2E em dispositivo real |
| AC-03 | Salvar e recuperar versões com propriedade correta | Persistência, conflito e autorização |
| AC-04 | Treino usa motor real e versões corretas | Resultado do motor e logs sanitizados |
| AC-05 | Bot inválido ou travado é contido | Timeout, falhas e limites |
| AC-06 | Robô não acessa arquivos pessoais, segredos, banco ou controle do host | Testes negativos do isolamento |
| AC-07 | Inscrição vincula versão imutável | Teste após fechamento/edição |
| AC-08 | Competição completa produz ranking correto | Fixtures e ensaio real |
| AC-09 | Retomadas não duplicam pontuação | Idempotência e recuperação |
| AC-10 | Interface utilizável em tela pequena | Toque, teclado, acessibilidade e rede definida |
| AC-11 | Host próprio tem restauração e rollback testados | Runbook executado |
| AC-12 | Capacidade e exposição respeitam medição e autorização | Relatório e aceite operacional |
| AC-13 | Requisitos obrigatórios cobertos por testes/evidências | Matriz de rastreabilidade |
| AC-14 | Piloto e pitch distinguem fatos e hipóteses | Revisão de homologação |

Sem autoria móvel, acompanhamento não atende ao objetivo. Sem motor real, mock não atende integração. Sem isolamento validado, não liberar execução não confiável. Sem restauração testada, funcionamento em desenvolvimento não equivale a implantação homologada.
