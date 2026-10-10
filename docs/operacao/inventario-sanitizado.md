# Inventário sanitizado — pré-implantação

**Estado:** levantamento preparado; dados locais ainda não verificados. **Tarefa:** S00-T05.

| Item | Informação disponível | Verificação necessária |
|---|---|---|
| Destino | Máquina própria, conforme decisão do responsável | Confirmar ambiente dedicado ao MVP |
| Processador | Intel Core i9, informado na discussão | Modelo, núcleos disponíveis e limites de uso |
| Memória | 128 GB, informados na discussão | Memória livre e reserva para uso pessoal |
| Sistema e virtualização | Não verificados nesta execução | Sistema/versão e suporte à VM/WSL/container |
| Armazenamento | Não medido | Espaço livre, volumes e reserva para logs/backups |
| Rede | Não levantada | Upload, estabilidade, acesso autorizado e restrições do provedor; não publicar IP |
| Disponibilidade | Não acordada | Janelas de funcionamento e interrupções aceitáveis |
| Backup | Não verificado | Destino separado e roteiro de restauração |

O script `scripts/collect_host_inventory.py` coleta somente dados técnicos básicos para `.local/inventory.json`, ignorado pelo Git. Não executar o script neste ambiente para fingir inventário da máquina alvo. Revisar localmente antes de compartilhar qualquer resumo. Não coletar nomes de usuários, hostname, endereços de rede, chaves, senhas ou arquivos pessoais.

Nenhuma porta, regra de firewall, túnel, serviço ou runner self-hosted foi configurado. Capacidade de alunos/batalhas será medida na S08, não inferida apenas de CPU e RAM.
