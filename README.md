# ETL com Prefect: MySQL para PostgreSQL (Incremental)

## Descrição

Este projeto ETL (Extrair, Transformar, Carregar) foi criado para transferir dados incrementais de um banco de dados MySQL para um banco de dados PostgreSQL utilizando Prefect. Além disso, o projeto oferece suporte para execução local e usando Docker.

O projeto mantém um histórico do último registro transferido para evitar a duplicação de dados.

## Pré-requisitos

- Python 3.7+
- Docker (opcional)
- MySQL e PostgreSQL rodando

## Instalação Local

### Passo 1: Clonar o repositório

```bash
git clone <link-do-repositório>
```

### Passo 2: Instalar Dependências

```bash
cd <diretório-do-projeto>
pip install -r requirements.txt
```

### Passo 3: Configurar Secrets

O projeto utiliza a funcionalidade de `Secrets` do Prefect para armazenar URLs de banco de dados. Certifique-se de criar dois secrets:

- `SOURCE_DB_URL`: para o banco de dados MySQL (por exemplo, `mysql+pymysql://root:rootpassword@localhost:3306/source_db`)
- `TARGET_DB_URL`: para o banco de dados PostgreSQL (por exemplo, `postgresql://target_user:mysecretpassword@localhost:5432/target_db`)


### Passo 4: Executar o ETL

```bash
python main.py
```

## Executando com Docker-Compose

### Passo 1: Construir o contêiner

```bash
docker-compose build
```

### Passo 2: Executar o serviço

```bash
docker-compose up
```

## Estrutura do Código

O código é dividido em duas tarefas principais:

1. **Extract Task**: Esta tarefa se conecta ao banco de dados MySQL e extrai todos os dados de tabelas que não são tabelas de sistema.

2. **Transform Task**: Transforma o esquema e os dados para serem compatíveis com o PostgreSQL. As seguintes transformações são aplicadas:

BINARY(n) para BYTEA

Obs: Outros tipos podem ser alterados.

3. **Load Task**: Esta tarefa faz o seguinte:
    - Cria uma tabela `etl_history_log` para manter o controle dos registros já transferidos.
    - Verifica a última entrada transferida de cada tabela.
    - Transfere novos registros para o PostgreSQL.
    - Atualiza a tabela `etl_history_log`.