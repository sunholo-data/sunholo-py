"use strict";(self.webpackChunkdocs=self.webpackChunkdocs||[]).push([[8560],{6668:(e,n,s)=>{s.r(n),s.d(n,{assets:()=>a,contentTitle:()=>c,default:()=>h,frontMatter:()=>i,metadata:()=>t,toc:()=>o});var l=s(4848),r=s(8453);const i={},c="alloydb_client.py",t={id:"sunholo/database/alloydb_client",title:"alloydb_client.py",description:"Source: sunholo/database/alloydbclient.py",source:"@site/docs/sunholo/database/alloydb_client.md",sourceDirName:"sunholo/database",slug:"/sunholo/database/alloydb_client",permalink:"/docs/sunholo/database/alloydb_client",draft:!1,unlisted:!1,editUrl:"https://github.com/sunholo-data/sunholo-py/tree/main/docs/docs/sunholo/database/alloydb_client.md",tags:[],version:"current",frontMatter:{},sidebar:"tutorialSidebar",previous:{title:"alloydb.py",permalink:"/docs/sunholo/database/alloydb"},next:{title:"static_dbs.py",permalink:"/docs/sunholo/database/static_dbs"}},a={},o=[{value:"Classes",id:"classes",level:2},{value:"AlloyDBClient",id:"alloydbclient",level:3}];function d(e){const n={a:"a",code:"code",em:"em",h1:"h1",h2:"h2",h3:"h3",li:"li",p:"p",pre:"pre",strong:"strong",ul:"ul",...(0,r.R)(),...e.components};return(0,l.jsxs)(l.Fragment,{children:[(0,l.jsx)(n.h1,{id:"alloydb_clientpy",children:"alloydb_client.py"}),"\n",(0,l.jsxs)(n.p,{children:[(0,l.jsx)(n.em,{children:"Source"}),": ",(0,l.jsx)(n.a,{href:"https://github.com/sunholo-data/sunholo-py/blob/main/sunholo/database/alloydb_client.py",children:"sunholo/database/alloydb_client.py"})]}),"\n",(0,l.jsx)(n.h2,{id:"classes",children:"Classes"}),"\n",(0,l.jsx)(n.h3,{id:"alloydbclient",children:"AlloyDBClient"}),"\n",(0,l.jsx)(n.p,{children:"A class to manage interactions with an AlloyDB instance."}),"\n",(0,l.jsx)(n.p,{children:"Example Usage:"}),"\n",(0,l.jsx)(n.pre,{children:(0,l.jsx)(n.code,{className:"language-python",children:'client = AlloyDBClient(\n    project_id="your-project-id",\n    region="your-region",\n    cluster_name="your-cluster-name",\n    instance_name="your-instance-name",\n    user="your-db-user",\n    password="your-db-password"\n)\n\n# Create a database\nclient.execute_sql("CREATE DATABASE my_database")\n\n# Execute other SQL statements\nclient.execute_sql("CREATE TABLE my_table (id INT, name VARCHAR(50))")\n'})}),"\n",(0,l.jsxs)(n.ul,{children:["\n",(0,l.jsxs)(n.li,{children:[(0,l.jsx)(n.strong,{children:"init"}),"(self, config: sunholo.utils.config_class.ConfigManager, project_id: str = None, region: str = None, cluster_name: str = None, instance_name: str = None, user: str = None, password: str = None, db='postgres')","\n",(0,l.jsxs)(n.ul,{children:["\n",(0,l.jsx)(n.li,{children:"Initializes the AlloyDB client."}),"\n"]}),"\n"]}),"\n"]}),"\n",(0,l.jsxs)(n.ul,{children:["\n",(0,l.jsx)(n.li,{children:"project_id (str): GCP project ID where the AlloyDB instance resides."}),"\n",(0,l.jsx)(n.li,{children:"region (str): The region where the AlloyDB instance is located."}),"\n",(0,l.jsx)(n.li,{children:"cluster_name (str): The name of the AlloyDB cluster."}),"\n",(0,l.jsx)(n.li,{children:"instance_name (str): The name of the AlloyDB instance."}),"\n",(0,l.jsx)(n.li,{children:"user (str): If user is None will use the default service email"}),"\n",(0,l.jsx)(n.li,{children:"db_name (str): The name of the database."}),"\n"]}),"\n",(0,l.jsxs)(n.ul,{children:["\n",(0,l.jsxs)(n.li,{children:["\n",(0,l.jsx)(n.p,{children:"_and_or_ilike(sources, search_type='OR', operator='ILIKE')"}),"\n",(0,l.jsxs)(n.ul,{children:["\n",(0,l.jsx)(n.li,{children:"No docstring available."}),"\n"]}),"\n"]}),"\n",(0,l.jsxs)(n.li,{children:["\n",(0,l.jsx)(n.p,{children:"_build_instance_uri(self, project_id, region, cluster_name, instance_name)"}),"\n",(0,l.jsxs)(n.ul,{children:["\n",(0,l.jsx)(n.li,{children:"No docstring available."}),"\n"]}),"\n"]}),"\n",(0,l.jsxs)(n.li,{children:["\n",(0,l.jsx)(n.p,{children:"_create_engine(self)"}),"\n",(0,l.jsxs)(n.ul,{children:["\n",(0,l.jsx)(n.li,{children:"No docstring available."}),"\n"]}),"\n"]}),"\n",(0,l.jsxs)(n.li,{children:["\n",(0,l.jsx)(n.p,{children:"_create_engine_from_pg8000(self, user, password, db)"}),"\n",(0,l.jsxs)(n.ul,{children:["\n",(0,l.jsx)(n.li,{children:"No docstring available."}),"\n"]}),"\n"]}),"\n",(0,l.jsxs)(n.li,{children:["\n",(0,l.jsx)(n.p,{children:"_execute_sql_async_langchain(self, sql_statement)"}),"\n",(0,l.jsxs)(n.ul,{children:["\n",(0,l.jsx)(n.li,{children:"No docstring available."}),"\n"]}),"\n"]}),"\n",(0,l.jsxs)(n.li,{children:["\n",(0,l.jsx)(n.p,{children:"_execute_sql_async_pg8000(self, sql_statement)"}),"\n",(0,l.jsxs)(n.ul,{children:["\n",(0,l.jsx)(n.li,{children:"Executes a given SQL statement asynchronously with error handling."}),"\n"]}),"\n"]}),"\n",(0,l.jsxs)(n.li,{children:["\n",(0,l.jsx)(n.p,{children:"_execute_sql_langchain(self, sql_statement)"}),"\n",(0,l.jsxs)(n.ul,{children:["\n",(0,l.jsx)(n.li,{children:"No docstring available."}),"\n"]}),"\n"]}),"\n",(0,l.jsxs)(n.li,{children:["\n",(0,l.jsx)(n.p,{children:"_execute_sql_pg8000(self, sql_statement)"}),"\n",(0,l.jsxs)(n.ul,{children:["\n",(0,l.jsx)(n.li,{children:"Executes a given SQL statement with error handling."}),"\n"]}),"\n"]}),"\n"]}),"\n",(0,l.jsxs)(n.ul,{children:["\n",(0,l.jsx)(n.li,{children:"sql_statement (str): The SQL statement to execute."}),"\n",(0,l.jsx)(n.li,{children:"Returns: The result of the execution, if any."}),"\n"]}),"\n",(0,l.jsxs)(n.ul,{children:["\n",(0,l.jsxs)(n.li,{children:["\n",(0,l.jsx)(n.p,{children:"_get_document_from_docstore(self, source: str, vector_name: str)"}),"\n",(0,l.jsxs)(n.ul,{children:["\n",(0,l.jsx)(n.li,{children:"No docstring available."}),"\n"]}),"\n"]}),"\n",(0,l.jsxs)(n.li,{children:["\n",(0,l.jsx)(n.p,{children:"_get_embedder(self, vector_name)"}),"\n",(0,l.jsxs)(n.ul,{children:["\n",(0,l.jsx)(n.li,{children:"No docstring available."}),"\n"]}),"\n"]}),"\n",(0,l.jsxs)(n.li,{children:["\n",(0,l.jsx)(n.p,{children:"_get_sources_from_docstore(self, sources, vector_name, search_type='OR')"}),"\n",(0,l.jsxs)(n.ul,{children:["\n",(0,l.jsx)(n.li,{children:"Helper function to build the SQL query for fetching sources."}),"\n"]}),"\n"]}),"\n",(0,l.jsxs)(n.li,{children:["\n",(0,l.jsx)(n.p,{children:"_list_sources_from_docstore(self, sources, vector_name, search_type='OR')"}),"\n",(0,l.jsxs)(n.ul,{children:["\n",(0,l.jsx)(n.li,{children:"Helper function to build the SQL query for listing sources."}),"\n"]}),"\n"]}),"\n",(0,l.jsxs)(n.li,{children:["\n",(0,l.jsx)(n.p,{children:"_similarity_search(self, query, source_filter: str = '', free_filter: str = None)"}),"\n",(0,l.jsxs)(n.ul,{children:["\n",(0,l.jsx)(n.li,{children:"No docstring available."}),"\n"]}),"\n"]}),"\n",(0,l.jsxs)(n.li,{children:["\n",(0,l.jsx)(n.p,{children:"asimilarity_search(self, query, source_filter: str = '', free_filter: str = None, k: int = 5)"}),"\n",(0,l.jsxs)(n.ul,{children:["\n",(0,l.jsx)(n.li,{children:"No docstring available."}),"\n"]}),"\n"]}),"\n",(0,l.jsxs)(n.li,{children:["\n",(0,l.jsx)(n.p,{children:"create_database(self, database_name)"}),"\n",(0,l.jsxs)(n.ul,{children:["\n",(0,l.jsx)(n.li,{children:"No docstring available."}),"\n"]}),"\n"]}),"\n",(0,l.jsxs)(n.li,{children:["\n",(0,l.jsx)(n.p,{children:"create_docstore_table(self, vector_name: str, users)"}),"\n",(0,l.jsxs)(n.ul,{children:["\n",(0,l.jsx)(n.li,{children:"No docstring available."}),"\n"]}),"\n"]}),"\n",(0,l.jsxs)(n.li,{children:["\n",(0,l.jsx)(n.p,{children:"create_schema(self, schema_name='public')"}),"\n",(0,l.jsxs)(n.ul,{children:["\n",(0,l.jsx)(n.li,{children:"No docstring available."}),"\n"]}),"\n"]}),"\n",(0,l.jsxs)(n.li,{children:["\n",(0,l.jsx)(n.p,{children:"create_tables(self, vector_name, users)"}),"\n",(0,l.jsxs)(n.ul,{children:["\n",(0,l.jsx)(n.li,{children:"No docstring available."}),"\n"]}),"\n"]}),"\n",(0,l.jsxs)(n.li,{children:["\n",(0,l.jsx)(n.p,{children:"create_vectorstore_table(self, vector_name: str, users)"}),"\n",(0,l.jsxs)(n.ul,{children:["\n",(0,l.jsx)(n.li,{children:"No docstring available."}),"\n"]}),"\n"]}),"\n",(0,l.jsxs)(n.li,{children:["\n",(0,l.jsx)(n.p,{children:"delete_sources_from_alloydb(self, sources, vector_name)"}),"\n",(0,l.jsxs)(n.ul,{children:["\n",(0,l.jsx)(n.li,{children:"Deletes from both vectorstore and docstore"}),"\n"]}),"\n"]}),"\n",(0,l.jsxs)(n.li,{children:["\n",(0,l.jsx)(n.p,{children:"execute_sql(self, sql_statement)"}),"\n",(0,l.jsxs)(n.ul,{children:["\n",(0,l.jsx)(n.li,{children:"No docstring available."}),"\n"]}),"\n"]}),"\n",(0,l.jsxs)(n.li,{children:["\n",(0,l.jsx)(n.p,{children:"execute_sql_async(self, sql_statement)"}),"\n",(0,l.jsxs)(n.ul,{children:["\n",(0,l.jsx)(n.li,{children:"No docstring available."}),"\n"]}),"\n"]}),"\n",(0,l.jsxs)(n.li,{children:["\n",(0,l.jsx)(n.p,{children:"fetch_owners(self)"}),"\n",(0,l.jsxs)(n.ul,{children:["\n",(0,l.jsx)(n.li,{children:"No docstring available."}),"\n"]}),"\n"]}),"\n",(0,l.jsxs)(n.li,{children:["\n",(0,l.jsx)(n.p,{children:"get_document_from_docstore(self, source: str, vector_name)"}),"\n",(0,l.jsxs)(n.ul,{children:["\n",(0,l.jsx)(n.li,{children:"No docstring available."}),"\n"]}),"\n"]}),"\n",(0,l.jsxs)(n.li,{children:["\n",(0,l.jsx)(n.p,{children:"get_document_from_docstore_async(self, source: str, vector_name: str)"}),"\n",(0,l.jsxs)(n.ul,{children:["\n",(0,l.jsx)(n.li,{children:"No docstring available."}),"\n"]}),"\n"]}),"\n",(0,l.jsxs)(n.li,{children:["\n",(0,l.jsx)(n.p,{children:"get_sources_from_docstore(self, sources, vector_name, search_type='OR', just_source_name=False)"}),"\n",(0,l.jsxs)(n.ul,{children:["\n",(0,l.jsx)(n.li,{children:"Fetches sources from the docstore."}),"\n"]}),"\n"]}),"\n",(0,l.jsxs)(n.li,{children:["\n",(0,l.jsx)(n.p,{children:"get_sources_from_docstore_async(self, sources, vector_name, search_type='OR', just_source_name=False)"}),"\n",(0,l.jsxs)(n.ul,{children:["\n",(0,l.jsx)(n.li,{children:"Fetches sources from the docstore asynchronously."}),"\n"]}),"\n"]}),"\n",(0,l.jsxs)(n.li,{children:["\n",(0,l.jsx)(n.p,{children:"get_vectorstore(self)"}),"\n",(0,l.jsxs)(n.ul,{children:["\n",(0,l.jsx)(n.li,{children:"No docstring available."}),"\n"]}),"\n"]}),"\n",(0,l.jsxs)(n.li,{children:["\n",(0,l.jsx)(n.p,{children:"grant_schema_permissions(self, schema_name, users)"}),"\n",(0,l.jsxs)(n.ul,{children:["\n",(0,l.jsx)(n.li,{children:"No docstring available."}),"\n"]}),"\n"]}),"\n",(0,l.jsxs)(n.li,{children:["\n",(0,l.jsx)(n.p,{children:"grant_table_permissions(self, table_name, users)"}),"\n",(0,l.jsxs)(n.ul,{children:["\n",(0,l.jsx)(n.li,{children:"No docstring available."}),"\n"]}),"\n"]}),"\n",(0,l.jsxs)(n.li,{children:["\n",(0,l.jsx)(n.p,{children:"similarity_search(self, query, source_filter: str = '', free_filter: str = None, k: int = 5)"}),"\n",(0,l.jsxs)(n.ul,{children:["\n",(0,l.jsx)(n.li,{children:"No docstring available."}),"\n"]}),"\n"]}),"\n"]})]})}function h(e={}){const{wrapper:n}={...(0,r.R)(),...e.components};return n?(0,l.jsx)(n,{...e,children:(0,l.jsx)(d,{...e})}):d(e)}},8453:(e,n,s)=>{s.d(n,{R:()=>c,x:()=>t});var l=s(6540);const r={},i=l.createContext(r);function c(e){const n=l.useContext(i);return l.useMemo((function(){return"function"==typeof e?e(n):{...n,...e}}),[n,e])}function t(e){let n;return n=e.disableParentContext?"function"==typeof e.components?e.components(r):e.components||r:c(e.components),l.createElement(i.Provider,{value:n},e.children)}}}]);