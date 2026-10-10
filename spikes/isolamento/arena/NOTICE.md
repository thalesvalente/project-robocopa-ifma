# Origem e atribuição — I2 / arena separada

O experimento usa **Robocode Tank Royale 1.4.0**, commit upstream `c8ad3a8d19a843f6258d6f6f9db7f29229963903`, sob licença Apache-2.0. Os arquivos de Walls e Spin Bot 1.0 são exemplos oficiais atribuídos a Mathew Nelson e Flemming N. Larsen, preservados sem alteração. A atribuição original e URLs estão também em [NOTICE do primeiro spike](../../tank-royale/NOTICE.md).

O JAR do servidor é extraído do `runner.jar` oficial previamente verificado, não reconstruído com patches. O cliente controlador Python e o gateway são código de integração da RoboCopa, não componentes apresentados como oficiais do upstream. O registro de replay é produzido pelo controlador a partir dos eventos oficiais recebidos; não foi testada sua reprodução no aplicativo gráfico oficial.

| Componente | Identificação imutável |
|---|---|
| Runner oficial | SHA-256 `02f6d1d8e9346a4aeae1b91e7abb278c98ac1f1d30c605f867758566f5f327cf` |
| Servidor extraído | SHA-256 `16c277795bd823c9eda0b650f1d09a418ff35cfe43d59b820c52d5e6816f905c` |
| Exemplos Java oficiais | SHA-256 `1707c1011a37c6b854fc79d68549ab204007bac6d33d803fa254152ac0765fe2` |
| WebSocket Python | `websockets==15.0.1`, wheel `f7a866fbc1e97b5c617ee4116daaa09b722101d4a3c170c787450ba409f9736f` |

A biblioteca `websockets` é de Aymeric Augustin e colaboradores, sob BSD-3-Clause. O wheel preserva seus avisos/licença. Imagens Python e Eclipse Temurin estão fixadas por digest no Dockerfile; suas licenças e as das dependências do motor continuam aplicáveis. Este documento não atribui uma nova licença geral à plataforma.

## Fontes primárias

- Release: https://github.com/robocode-dev/tank-royale/releases/tag/v1.4.0
- Apache-2.0 upstream: https://github.com/robocode-dev/tank-royale/blob/c8ad3a8d19a843f6258d6f6f9db7f29229963903/LICENSE
- Handshake e despacho por tipo: https://github.com/robocode-dev/tank-royale/blob/c8ad3a8d19a843f6258d6f6f9db7f29229963903/server/src/main/kotlin/dev/robocode/tankroyale/server/connection/ClientWebSocketsHandler.kt
- Licença websockets15.0.1: https://github.com/python-websockets/websockets/blob/15.0.1/LICENSE
- API WebSocket síncrona: https://websockets.readthedocs.io/en/15.0.1/reference/sync/server.html

Digests identificam os bytes utilizados; não demonstram ausência de vulnerabilidades nem autenticidade de um árbitro comprometido. Antes de distribuição/implantação, revisar avisos e atualizações de todos os componentes.
