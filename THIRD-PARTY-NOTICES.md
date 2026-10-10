# Componentes e avisos de terceiros

## GitHub Spec Kit

Origem: https://github.com/github/spec-kit

Release: v1.1.2. Commit fixado: `959e866caa3618bf3dc290d5dca33394365af9c6`.

A inicialização oficial gerou scripts, templates e comandos sob `.specify/` e `.agents/`. A constituição do projeto foi preservada, e não é o texto-modelo original. O manifesto da geração está em `docs/qualidade/evidencias/SPECKIT-CI.json`.

Licença: MIT; Copyright GitHub, Inc. O texto integral foi preservado em [licenses/spec-kit-MIT.txt](licenses/spec-kit-MIT.txt), obtido de https://github.com/github/spec-kit/blob/959e866caa3618bf3dc290d5dca33394365af9c6/LICENSE.

Este aviso não atribui automaticamente a licença MIT ao código e aos documentos próprios da RoboCopa IFMA. A licença geral do projeto ainda não foi definida pelo responsável. Componentes futuros, inclusive motor e editor, devem ser avaliados nas versões efetivamente incorporadas.

## Dependências do adaptador PostgreSQL I3-03B

Psycopg **3.3.6** (LGPL-3.0-only), https://pypi.org/project/psycopg/3.3.6/, e typing_extensions **4.15.0** (PSF-2.0), https://pypi.org/project/typing_extensions/4.15.0/, são instalados no ambiente de integração a partir do PyPI com versões/hashes em `services/execution_control/postgres/requirements.txt`. Não há cópia vendorizada de código desses pacotes no repositório; seus wheels preservam licenças e metadados. A adoção não relicencia a RoboCopa nem significa que um produto distribuído futuro já cumpre todas as obrigações aplicáveis. Rever distribuição/empacotamento antes da entrega pública.

A biblioteca `libpq` do sistema operacional é dependência de execução do driver no runner. Nenhuma biblioteca PostgreSQL foi instalada no computador pessoal do responsável. Código do adaptador segue o contrato Psycopg, mas a importação e instalação do driver ocorrem apenas no ambiente configurado de serviço/teste.
