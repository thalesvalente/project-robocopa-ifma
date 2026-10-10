# Origem e atribuição

Este experimento utiliza **Robocode Tank Royale 1.4.0**, de robocode-dev, commit `c8ad3a8d19a843f6258d6f6f9db7f29229963903`, sob licença Apache-2.0, conforme o arquivo LICENSE do upstream.

- Release: https://github.com/robocode-dev/tank-royale/releases/tag/v1.4.0
- Licença: https://github.com/robocode-dev/tank-royale/blob/v1.4.0/LICENSE
- Exemplo da API Runner: https://github.com/robocode-dev/tank-royale/blob/v1.4.0/runner/examples/RunBattle.java
- Amostras: https://github.com/robocode-dev/tank-royale/tree/v1.4.0/sample-bots/java

Os metadados dos bots **Walls** e **Spin Bot** atribuem autoria a **Mathew Nelson** e **Flemming N. Larsen**, versão 1.0, licença Apache-2.0. Seus arquivos de origem e metadados são usados sem alteração. A pasta `SpinBot` declara o nome `Spin Bot`; ambos são preservados em seus respectivos papéis.

`upstream.lock.json` registra URLs, tamanhos e SHA-256 dos dois arquivos publicados. Os binários upstream não são commitados neste repositório: são obtidos e verificados durante a construção local/CI. O pacote de amostras conserva os arquivos e avisos fornecidos pelo upstream. A licença upstream não deve ser confundida com a licença geral da plataforma RoboCopa.

O wrapper `SpikeBattle.java` e os scripts Python integram o experimento da RoboCopa; não são apresentados como componentes oficiais do Tank Royale. As imagens Python e Eclipse Temurin são dependências de execução, fixadas por digest no Dockerfile.
