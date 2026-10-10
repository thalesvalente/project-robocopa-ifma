# Revisão externa da arquitetura de isolamento — 10/10/2026

**Resultado da pesquisa:** a direção de uma VM Linux dedicada é coerente com o objetivo de proteger o computador pessoal, mas **uma VM sozinha não comprova segurança**. É necessário corrigir algumas simplificações do plano anterior e testar cada fronteira.

**Origem das conclusões:** fontes primárias consultadas na web e código upstream fixado do Tank Royale, separados abaixo de nossas inferências de projeto. Esta pesquisa não verifica o estado de atualização do Windows/Docker Desktop do responsável nem homologa produção.

## 1. VM própria, não outra distribuição WSL

**Fonte:** a documentação Docker informa que distribuições WSL 2 compartilham um kernel e recomenda avaliar Hyper-V para isolamento mais estrito. [S1](https://docs.docker.com/desktop/features/wsl/)

**Decisão de projeto:** manter o Docker Desktop existente intacto para os outros projetos. Para os robôs, preferir uma VM Linux independente, com sistema, disco virtual e daemon próprios. Criar outra distribuição Ubuntu no WSL não equivale à fronteira pretendida. A aprovação do responsável resolve a direção D2, não a instalação ou a prova de contenção.

**Limite:** hipervisor, kernel e runtime ainda precisam de atualização e configuração. Administradores do host continuam pertencendo à base de confiança; a VM não deve ser descrita como impermeável a qualquer vulnerabilidade.

## 2. Sem socket Docker é necessário, mas não suficiente

**Fonte:** Docker alerta que controle do daemon permite montar e alterar arquivos do host, e pede cuidado adicional quando uma aplicação web provisiona contêineres. [S2](https://docs.docker.com/engine/security/)

**Fonte adicional:** o aviso oficial CVE-2025-9074 descreve acesso indevido ao Engine a partir de contêineres Docker Desktop mesmo sem socket montado, corrigido em Desktop 4.44.3. Não se aplica automaticamente a toda instalação atual, mas demonstra que verificar somente mounts não é prova suficiente. [S3](https://docs.docker.com/security/security-announcements/)

**Consequência:** não expor o servidor Python de laboratório que chama a CLI Docker. Manter API, banco, credenciais administrativas e worker separados; verificar também canais de rede e superfície do daemon. O Engine 28.1.1 informado no inventário **não identifica a versão do produto Docker Desktop**. A revisão de atualização do Desktop/Windows/WSL é pendência antes de instalação no host; não declarar a máquina vulnerável só pelo número do Engine.

## 3. Rede interna não significa inacessibilidade do host

**Fonte:** uma bridge Docker permite comunicação entre seus integrantes; portas não publicadas podem estar acessíveis a contêineres da mesma rede. [S4](https://docs.docker.com/engine/network/drivers/bridge/)

**Fonte:** Hyper-V diferencia switch External, Internal (inclui host↔VM) e Private (somente VMs). [S5](https://learn.microsoft.com/en-us/windows-server/virtualization/hyper-v/plan/plan-hyper-v-networking-in-windows-server)

**Correção do plano:** não aceitar `internal:true`, NAT ou `--network none` como substitutos intercambiáveis. O modo `none` é adequado às primeiras sondas de contenção, mas não valida a futura comunicação WebSocket bot↔árbitro. A rede de jogo precisará de controles específicos, identidades distintas e teste positivo de comunicação permitida, além de negativos de host/LAN/serviços administrativos. Não criar automaticamente switch External ou reutilizar o Default Switch para alegar isolamento.

## 4. Rootless e gVisor são camadas, não requisitos cegos

**Fonte:** rootless remove privilégios de root tanto do daemon quanto dos contêineres; userns-remap remapeia usuários, mas o daemon permanece privilegiado. [S6](https://docs.docker.com/engine/security/rootless/)

**Fonte:** gVisor acrescenta defesa contra exploração do kernel e documenta seu modelo de ameaças e limitações. [S7](https://gvisor.dev/docs/architecture_guide/security/)

**Aplicação:** avaliar essas camadas dentro da VM, com compatibilidade e quotas observadas. Não acrescentar gVisor, Kubernetes ou microVM por padrão ao MVP básico sem ganho demonstrado. A primeira bateria pode usar runc no runner descartável para verificar os controles explícitos; isso não aprova o runtime final nem a proteção do host.

## 5. Quotas incluem swap, disco temporário e saída

**Fonte:** contêineres não recebem limites de recursos por padrão. Docker explica que memória e swap são controles diferentes; `--memory-swap` igual a `--memory` impede swap adicional quando suportado. [S8](https://docs.docker.com/engine/containers/resource_constraints/)

**Mudança planejada:** limites observáveis de CPU, RAM+swap, PIDs e tmpfs; timeout externo; leitura de stdout/stderr limitada **durante a transferência**, não apenas depois de salvar um arquivo enorme. Inspeção da configuração e leitura de cgroups/seccomp dentro do processo devem ser combinadas com sondas positivas/negativas. As quotas pequenas da bateria não serão anunciadas como capacidade de partidas do MVP.

## 6. Tank Royale suporta servidor externo; isso não externaliza os bots

**Fonte web:** a API Battle Runner oferece servidor embutido ou externo e gerencia o ciclo das partidas. [S9](https://robocode.dev/api/battle-runner.html)

**Fonte versionada:** em Tank Royale 1.4.0, `BattleRunner.startBattleAsync` valida diretórios de bots e chama `BooterManager.boot(...)` mesmo com servidor externo. Esse comportamento foi lido no commit c8ad3a8d19a843f6258d6f6f9db7f29229963903, linhas 145–191. [S10](https://github.com/robocode-dev/tank-royale/blob/c8ad3a8d19a843f6258d6f6f9db7f29229963903/runner/src/main/kotlin/dev/robocode/tankroyale/runner/BattleRunner.kt)

**Correção importante:** trocar apenas `embeddedServer()` por `externalServer()` não implementa automaticamente bot em sandbox separado do controlador. A prova T007 precisa de estratégia explícita de inicialização e controle, segredos de papéis distintos e verificação dos resultados do árbitro. Não fornecer Docker socket ao booter para contornar essa limitação. A integração deverá preservar a versão fixada ou justificar alteração de versão com regressão.

**Fonte complementar:** a documentação atual descreve segredos de bots e controladores; não presumir que autenticação esteja habilitada só porque campos existem. [S11](https://robocode.dev/articles/configuration-files.html) e [S12](https://robocode.dev/articles/debug.html). A implementação deverá verificar o comportamento contra o artefato 1.4.0, não só contra a documentação corrente.

## 7. Integridade não é apenas SHA-256

**Inferência de segurança do projeto:** hashes verificam consistência de bytes; não autenticam um resultado se o atacante controlar tanto o arquivo quanto o manifesto. Por isso a fonte do placar deve ser um árbitro separado da estratégia, com canal administrativo inacessível ao bot, vínculo a job/versão e controle de tentativas. Comparar dois arquivos produzidos no mesmo ambiente comprometido não seria uma prova independente de honestidade.

O contrato inicial será implementado sem endpoint público: campos estritos, linguagem/versão autorizadas, hash de texto e AST, prazo, idempotency key e rejeição antes de qualquer chamada ao Docker. Autenticação multiusuário, broker remoto e ledger durável continuam tarefas posteriores.

## 8. Por que usar CI descartável primeiro

**Fonte:** GitHub informa que runners hospedados padrão (exceto a modalidade de um único CPU) usam uma nova VM por job; virtualização aninhada não possui garantia de suporte. [S13](https://docs.github.com/en/actions/concepts/runners/github-hosted-runners)

**Decisão:** executar sondas pequenas em Ubuntu GitHub-hosted, sem segredos fornecidos à carga, sem runner self-hosted e sem VM aninhada. Isso testa Linux/container **no runner**, não Hyper-V, VHDX, rede nem recuperação do Windows do responsável. A bateria recusará execução local/WSL/Docker Desktop para evitar uso acidental. Essa trava é operacional, não atestado criptográfico: variáveis de ambiente podem ser forjadas por um operador com controle do processo.

## Conclusão e próximos marcos

1. Direção D2 confirmada: VM dedicada e daemon independente, mantendo o computador e outros projetos fora do caminho de execução de alunos.
2. D1 preservada: RoboDSL básica; recursos intermediários/avançados pós-MVP. A DSL continua entrada não confiável.
3. Esta rodada começa por contrato de admissão, política de runtime, transporte limitado, sondas sintéticas e limpeza. Não tenta explorar CVEs ou ler arquivos pessoais.
4. T007 — separação real bot/árbitro — continua um teste de compatibilidade específico; documentação de servidor externo não o resolve.
5. Antes de alunos: VM real, atualizações, broker/autorização, rede permitida, replay confiável, quotas calibradas, fila/recuperação, backup/restore, teste físico móvel e aceite de liberação.

**Não ocorreu:** implantação da VM, modificação de firewall/WSL/Docker Desktop, acesso ao computador pessoal, liberação pública ou homologação de segurança. O resultado da pesquisa é favorável à direção, com as correções acima.
