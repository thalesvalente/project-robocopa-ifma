# Inventário do computador hospedeiro (S00-T05)

Este coletor **não instala nada**, **não altera serviços ou portas**, **não precisa de administrador** e **não realiza testes pela internet**. A execução acontece apenas no computador do responsável pelo projeto.

## Como executar no Windows 11 (PowerShell)

No diretório clonado do projeto e na branch de trabalho:

```powershell
git fetch origin
git switch chore/s00-fundacao-speckit
git pull --ff-only
python scripts/collect_host_inventory.py
Get-Content .local/inventory-v3.json
```

Se o comando `python` não estiver disponível, utilize `py`. Não é necessário ativar um ambiente virtual. O script usa apenas a biblioteca padrão do Python.

## Dados técnicos coletados

- Processador: modelo, núcleos físicos e lógicos, estado da virtualização em firmware (quando informado pelo Windows).
- Memória: quantidade instalada, memória livre no instante da coleta e informações de capacidade/velocidade dos módulos.
- GPU: modelo e versão do driver; VRAM de GPUs NVIDIA se `nvidia-smi` estiver acessível.
- Armazenamento: volumes locais, espaço disponível, modelos/tipo/capacidade dos discos quando o Windows disponibilizar.
- Windows: edição, build, tempo desde a inicialização e presença de hipervisor.
- Docker: distingue CLI instalada de daemon acessível; coleta versão, CPU/RAM disponíveis, versão do Compose, caminho interno do daemon (sanitizado) e uso por imagens, contêineres, volumes e cache via `docker system df --format json`.
- O levantamento de uso Docker é apenas leitura, mas pode ser mais lento em hosts com muitas imagens/volumes; há limite de tempo e retorno parcial se falhar.
- WSL: distribuição padrão, versão padrão, versões e estado (ativa/parada) das distribuições via `wsl --status` e `wsl --list --verbose`. Apenas nomes comuns (Ubuntu, docker-desktop etc.) são mantidos; nomes personalizados são substituídos por `[custom_name_redacted]`.
- Rede local: velocidade negociada do adaptador físico ativo, estados dos perfis do firewall e se algumas portas comuns estão ocupadas. **Isso não equivale à velocidade de upload nem à confirmação de acesso público.**
- Ferramentas: disponibilidade de comandos para Git, Docker, WSL, Node, Java e outras.

Se alguma sondagem falhar ou não estiver disponível, o resultado registra status parcial, não um falso diagnóstico positivo.

## Privacidade e segurança

O arquivo é salvo em **`.local/inventory-v3.json`**, mantido fora do versionamento. Os arquivos anteriores `.local/inventory.json` e `.local/inventory-v2.json` são preservados. O programa recusa substituir o inventário v3 já existente: renomeie-o ou mova-o após revisar para uma nova coleta.

**Não coletamos:** hostname, nome de usuário, IP público/privado, endereço MAC, identificadores de hardware, SSID Wi-Fi, credenciais, nomes de processos ou contêineres, nomes personalizados de distribuições WSL, caminhos personalizados do daemon e arquivos pessoais. A execução de sondas de Docker e WSL também não armazena mensagens brutas de erro.

Revise o JSON antes de anexá-lo à conversa e **não faça commit do inventário**.

## O que ainda depende de checagem manual

1. Upload real e estabilidade da conexão de internet.
2. CGNAT, IPv4/IPv6 público, restrições e política do provedor.
3. Disponibilidade da máquina/energia e estratégia contra suspensão automática.
4. Política de isolamento/limites para código submetido pelos alunos.
5. Backup e teste de restauração, inclusive em unidade externa.
6. Capacidade aceitável de armazenamento considerando crescimento de banco, imagens, logs e resultados.
7. **Local físico do arquivo de disco virtual do Docker Desktop no Windows**: `Docker Desktop > Settings > Resources > Advanced > Disk image location`. O caminho Linux `/var/lib/docker` não informa a unidade Windows onde o VHDX está armazenado. Não mova o disco nem execute `docker system prune` durante o inventário.

Não abra portas do roteador nem desative o firewall com base apenas neste relatório. A topologia e o controle de acesso remoto serão decididos na S04 após análise de risco.
