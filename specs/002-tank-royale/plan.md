# Plano técnico — Feature 002

Usar o Battle Runner JVM oficial em vez de reimplementar o protocolo WebSocket. O JAR publicado agrega servidor/booter e controla seu ciclo de vida. Wrapper Java chama startBattleAsync/awaitResults, acompanha eventos e grava os scores oficiais e replay; Python controla somente a imagem/contêiner e valida evidências. Não há dependência de Maven, npm ou Java local: Python e Docker já existentes bastam.

Release 1.4.0, commit upstream e hashes dos dois assets (runner e amostras Java) fixados. Imagens base também fixadas por digest observado no CI. Construção multi-stage verifica tamanho/SHA e extração ZIP, compila wrapper. Runtime: Java 21, UID 10001, rede none, root readonly, tmpfs limitado, sem binds/ports, 2 CPUs, 2 GiB, 256 PIDs. Registrar o ID da imagem; não alegar build bit-a-bit reprodutível.

Cinco rounds Classic por batalha, duas execuções independentes em CI, prazo de 240 segundos por execução. Exportar os bytes exatos do resultado e replay por stdout ANTES de o contêiner encerrar: tmpfs desaparece ao parar, portanto docker cp de um contêiner parado não serve aqui. Decodificar apenas nomes de arquivos permitidos em .local/tank-royale/<execucao>, sem montar diretórios do host. Remover só o contêiner criado nesta invocação. Preservar Compose/PostgreSQL/sonda.

Validadores/checksums/traversal/transporte testados offline; build e duas batalhas reais em GitHub-hosted Ubuntu. JSON, replay gzip, limpeza e política Docker efetiva precisam passar. Artifacts por 30 dias. Execução no Windows é aceite posterior. Preservar gates S03/S04. A identidade declarada do diretório SpinBot é 'Spin Bot' v1.0; não alterar o nome que o motor retorna.
