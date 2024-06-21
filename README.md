# oci_rag_sample_kit

# 概要
このコードkitはOCI上でOCI Generative AIとOracle Database 23aiを使い、RAGの技術を応用したチャットアプリを作成するコードです。このkitを実行すると以下の画像のようなチャットアプリを構築することができます。[こちら](https://qiita.com/sh-sho/items/b0afa8452f4790053a69)のQiitaで使用しているコードです。

<img src="https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/2633103/894fa427-7928-dfae-180f-8828a0739278.png" width="100%">

# アーキテクチャ
以下のようなアーキテクチャを考えます。Base Databaseにpdfのデータをベクトル化して保存します。Virtual Machine上でベクトル検索を行うAPIの提供とチャット画面となるアプリを起動させます。
![rag_architecture_detail.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/2633103/555acb0b-fa23-f35c-d61e-80def661ed10.png)

# 前提
* Oracle Cloud Infrastructureの環境
  * ネットワークリソースの構築
  * Virtual Machineの構築
  * Oracle Base Database 23aiの構築
  * Chicago or Frankfurt Regionのサブスクライブ
* Virtual Machineの環境構築
  * Python環境
  * oci-sdkが利用できる環境


# 手順
0. [事前準備](#0-事前準備)
1. [Tableの作成](#1-tableの作成)
2. [pdfデータのInsert](#2-pdfデータのinsert)
3. [Textデータのベクトル化](#3-textデータのベクトル化)
4. [ベクトル検索](#4-ベクトル検索)
5. [FAST APIを使ったAPI作成](#5-fast-apiを使ったapi作成)
6. [Streamlitを使ったフロントエンドの作成](#6-streamlit)
7. [Table削除](#7-tableの削除)


## OCIの環境構築
以下の内容は上記のアーキテクチャを構築した上で実行してください。

### GitリポジトリのClone
今回使うソースコードはこのGitHubに公開しています。

https://github.com/sh-sho/oci_rag_sample_kit

ご自身の環境にGitリポジトリをCloneします。
```bash
$ git clone https://github.com/sh-sho/oci_rag_sample_kit.git
```
`src`ディレクトリで作業を行います。
```bash
$ cd oci_rag_sample_kit/src/
$ tree -a
.
├── .env.example
├── 01.create_table.py
├── 02.insert_data.py
├── 03.embed_save_texts.py
├── 04.execute_vector_search.py
├── 05.vector_search_api.py
├── 06.front_app_streamlit.py
├── 07.drop_table.py
├── chatclass.py
├── data
│   ├── autonomous-database-self-securing-wp-ja.pdf
│   ├── oracle-cloud-infrastructure-waf-data-sheet-ja.pdf
│   └── oracle-gov-cloud-oci-ja.pdf
├── requirements.txt
├── table_detail.py
└── utils.py

1 directory, 15 files
```
### Python環境
Virtual MachineにPythonをインストールして実行環境を作成してください。
Python 3.11.9で動作確認済みです。
```bash
$ python --version
Python 3.11.9
```

`requirements.txt`に必要なライブラリが記載されているので以下のコマンドでインストールをします。
```bash
$ pip install -r requirements.txt
```
Vector Searchを行うため`python-oracledb`のバージョンは2.2.1以上のものを使用してください。

### 環境変数の設定
次に環境変数を設定します。
`.env.example`ファイルをコピーして`.env`ファイルを作成します。
```bash
$ cp .env.example .env
```
`.env`の内容をご自身の環境に合わせて書き換えます。
```
UN=username
PW=password
DSN=dsn
OCI_CONFIG_FILE=~/.oci/config
OCI_COMPARTMENT_ID=ocid1.compartment.oc1..aaaaaaaaxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
CSV_DIRECTORY_PATH=/tmp_data
CONFIG_PROFILE=CHICAGO
PDF_DIRECTORY_PATH='./data/'
```
`CONFIG_PROFILE`はOCI Generative AIをCallする際に使用するのでChicago (or Frankfurt) RegionのProfile名を指定してください。

# 1. Tableの作成
`01.create_table.py`のコードを実行すると、以下の３つのTableがBase Databaseに作成されます。

`SOURCE_TABLE`

| Column名 | Data Type | Size |
| ---- | -----    | ----     |
| ID   | NUMBER | 9 |
| NAME | VARCHAR2 | 100 BYTE |

`DOCUMENT_TABLE`

| Column名 | Data Type | Size |
| ----| -----| ---- |
| ID | NUMBER | 9 |
| DOCUMENT | CLOB |  |

`CHUNK_TABLE`

| Column名 | Data Type | Size |
| ----| -----| ---- |
| ID | NUMBER | 9 |
| CHUNK_ID | NUMBER |  |
| CHUNK | VARCHAR2 | 2000 BYTE |
| VECTOR | VECTOR |  |

コードを実行すると以下のような内容が出力されます。
```bash
$ python 01.create_table.py 
Start Creating Table.
End Creating Table.
```

# 2. pdfデータのInsert
`data/`配下のpdfのデータをTableにInsertします。
`data/`配下には以下のようなサンプルのpdfが置かれています。
```bash
$ tree ./data/
./data/
├── autonomous-database-self-securing-wp-ja.pdf # Autonomous Databaseに関する資料
├── oracle-cloud-infrastructure-waf-data-sheet-ja.pdf # OCI WAFに関する資料
└── oracle-gov-cloud-oci-ja.pdf # OCIの概要資料

0 directories, 3 files
```

実行すると、以下の内容が出力されます。
```bash
$ python 02.insert_data.py 
Start Insert data.
Insert data 1 to table1
Insert data 1 to table2
Insert data 2 to table1
Insert data 2 to table2
Insert data 3 to table1
Insert data 3 to table2
End Insert data
```

# 3. Textデータのベクトル化
pdfのデータをchunkに分割しベクトル化してTableに保存します
`03.embed_save_texts.py`のコードを実行すると、以下のような出力が得られます。
```bash
$ python 03.embed_save_texts.py 
...
0.0202178955078125, 0.052215576171875, 0.03814697265625, -0.035491943359375]))]
Total Run Time  1.683833360671997
success delete csv directory
```

# 4. ベクトル検索
Chunkに分割したpdfデータに対してベクトル検索を行います。
`04.execute_vector_search.py`コードと質問を入力して実行すると、以下ような内容が出力されます。
```bash
$ python 04.execute_vector_search.py 'Autonomous Databaseの高可用性について教えて'
Search Query：Autonomous Databaseの高可用性について教えて
Start Vector Search
============Result============
1: (2, 'autonomous-database-self-securing-wp-ja.pdf', '自己修復：Autonomous Databaseにより、あらゆる計画外および計画停止時間に対する予防的な保護が提供され、停止時間なしに障害から迅速に自動リカバリできます。\n\nAutonomous Databaseの可用性とパフォーマンスの管理は、AIベースの自律性を使用して次のレベルへと進みます。これによって複数の領域の診断が統合され、実行時に分析して措\n\n置を講じることができるようになり、操作の中断を最小限に抑えるか排除できます。\n\n図1：Oracle CloudのAutonomous Databaseコンポーネント\n\n自己修復の必要性について\n\nあらゆる規模の組織が、停止時間やデータ損失、データ・アクセスに影響を与えるパフォーマンスのボトルネックに関連するリスクについて詳しく知るようになってきています。90 %以上の企業が、', 0.32765958104735404)
2: (2, 'autonomous-database-self-securing-wp-ja.pdf', '9\n\n技術概要 | Oracle Autonomous Database\n\nCopyright © 2020, Oracle and/or its affiliates | 公開\n\nこの実績あるアーキテクチャは、世界中の何千ものインストールをサポートしており、これにはFortune 100企業が運用する世界的にも最もミッション・クリティカルなデータベースも 含まれます。\n\n他の自律機能と連携する自己修復', 0.3282624711042831)
3: (2, 'autonomous-database-self-securing-wp-ja.pdf', 'さまざまな問題を防止して修復します。Oracle Autonomous Databaseが提供するこの自己修復機能のコレクションは、業界の他のどのクラウド（またはオンプレミス）データベースの 追随も許しません。', 0.33745563121903666)
================================
End Vector Search
```

# 5. Fast APIを使ったAPI作成
入力された質問に対して、pdfをもとに回答を生成するチャットアプリを作ります。
バックエンドはFast APIで作成します。

`05.vector_search_api.py`のコードを実行してAPIを提供させます。
```python
$ python 05.vector_search_api.py 
INFO:     Started server process [81175]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

# 6. Streamlitを使ったフロントエンドの作成
Streamlitを使って、簡易的なチャットアプリのフロントエンドを作成します。
別のbashを開き、`06.front_app_streamlit.py`のコードを実行すると以下のような出力とアプリを作成することができます。
```bash
$ streamlit run 06.front_app_streamlit.py

Collecting usage statistics. To deactivate, set browser.gatherUsageStats to false.


  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
```

`http://localhost:8501`に接続しすると、以下のようなアプリの画面が作成されます。
<img src="https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/2633103/944778c7-a9e9-f369-cbe8-ce24b47bd039.png" width="100%">

# 7. Tableの削除
`05.drop_table.py`を実行し作成したTableを削除します。
実行すると以下の内容が出力されます。

```bash
$ python 05.drop_table.py 
Start Drop Table
Drop Table CHUNK_TABLE
Drop Table DOCUMENT_TABLE
Drop Table SOURCE_TABLE
End Drop Table
```
