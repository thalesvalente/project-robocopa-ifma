# Plano técnico — Feature 002

Usar o Battle Runner JVM oficial em vez de reimplementar o protocolo WebSocket. O JAR publicado agrega servidor/booter e controla seu ciclo de vida. Wrapper Java chama startBattleAsync/awaitResults, acompanha eventos e grava os scores oficiais e replay; Python controla somente a imagem/contêiner e valida evidências. Não há dependência de Maven, npm, Java local ou Codex para o usuário: Python e Docker já existentes bastam.

Congelar release 1.4.0, commit upstream e hashes dos dois assets (runner e amostras Java), consultados no upstream. Construção Docker multi-stage verifica tamanho/SHA e extração ZIP, compila wrapper. Runtime: Java 21, UID 10001, rede none, root readonly, tmpfs limitado, sem binds/ports, 2 CPUs, 2 GiB, 256 PIDs. A imagem base tem tag de versão; o ID da imagem efetivamente executada é registrado, sem alegar build bit-a-bit reprodutível.

Tratar bots de referência como código conhecido, não como simulação. Cinco rounds Classic por batalha, duas execuções independentes em CI, prazo global de 240 segundos por execução. Após término, docker cp copia somente /tmp/evidence para .local; remover apenas o contêiner criado nesta invocação. Não alterar o laboratório PostgreSQL/sonda.

Testar offline os validadores/checksums/traversal, depois build e batalha real em GitHub-hosted Ubuntu. Validar JSON, replay gzip e configuração efetiva Docker, anexando evidências sintéticas ao run por 30 dias. A execução no host do responsável é um aceite posterior. Preservar S03/S04 e registrar preparação técnica autorizada sem marcar arquitetura integralmente aprovada.
