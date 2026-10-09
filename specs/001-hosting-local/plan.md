# Plano técnico — Feature 001

**Estado:** candidato preparatório. **Base:** S00 publicada, inventário v3 local fornecido pelo responsável.

## A. Tecnologias e recorte

- `compose.local.yaml` com PostgreSQL 17 em rede interna e volume persistente, sonda HTTP Node 24 em loopback e redes separadas.
- Imagens oficiais em tags de versão principal, passíveis de atualização de patch; digests imutáveis serão avaliados antes de promoção à implantação de longo prazo.
- Segredo gerado em `.env` ignorado pelo Git, sem senha padrão incorporada ao Compose.
- Sem Redis inicial. Proposta de fila persistente futura no PostgreSQL; não implementar sem S03/S04.
- Teste de HTTP básico e de SQL em ambiente GitHub-hosted, não em máquina do responsável.

## B. Mudanças permitidas e responsabilidade

Criar `compose.local.yaml`, `infra/probe/`, scripts de inicialização/validação, suíte de infraestrutura, workflow próprio, ADRs e manual. Não mudar contêineres, imagens ou volumes existentes do host; não abrir redes nem apagar artefatos do responsável.

## C. Segurança

Validar publicação exclusiva 127.0.0.1, banco sem `ports`, rede de dados `internal:true`, limites por serviço, ausência de Docker socket e probe como usuário não root com filesystem readonly. O banco roda pela imagem oficial e precisa escrever no volume; não aplicar a ele restrições incompatíveis com a inicialização da imagem sem testes.

## D. Testes

1. Testes Python stdlib em `tests/infra` para rejeitar configuração pública, socket Docker, banco sem volume e limites ausentes.
2. Criar credencial local temporária no GitHub runner.
3. Executar `docker compose config --quiet` e análise do Compose normalizado.
4. Subir serviços com `--wait`, verificar `/health` e 404.
5. Criar tabela de teste e recriar contêiner do banco preservando o volume.
6. Desligar/limpar **apenas no runner descartável do CI**, no bloco `if: always()`.
7. Solicitar validação real no host e registrar evidência separada.

## E. Riscos e pendências

Conflito de nome de projeto, porta 18080 ocupada, Docker Desktop não iniciado, unidade do Docker sem espaço, CPU consumida por outros projetos, backup ausente, disponibilidade limitada e ausência de sandbox. A sonda não tem autorização para ficar acessível fora do loopback. O DockerRoot interno não determina o disco físico Windows.

**Próxima decisão:** aprovar arquitetura depois das especificações e spikes. Infraestrutura candidata pode existir sem marcar S04-T01/T05 como concluídas.
