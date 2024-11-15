"use strict";(self.webpackChunkdocs=self.webpackChunkdocs||[]).push([[5890],{7570:(n,e,i)=>{i.r(e),i.d(e,{assets:()=>t,contentTitle:()=>c,default:()=>h,frontMatter:()=>l,metadata:()=>r,toc:()=>a});var s=i(4848),o=i(8453);const l={},c="config_class.py",r={id:"sunholo/utils/config_class",title:"config_class.py",description:"Source: sunholo/utils/configclass.py",source:"@site/docs/sunholo/utils/config_class.md",sourceDirName:"sunholo/utils",slug:"/sunholo/utils/config_class",permalink:"/docs/sunholo/utils/config_class",draft:!1,unlisted:!1,editUrl:"https://github.com/sunholo-data/sunholo-py/tree/main/docs/docs/sunholo/utils/config_class.md",tags:[],version:"current",frontMatter:{},sidebar:"tutorialSidebar",previous:{title:"config.py",permalink:"/docs/sunholo/utils/config"},next:{title:"gcp.py",permalink:"/docs/sunholo/utils/gcp"}},t={},a=[{value:"Classes",id:"classes",level:2},{value:"ConfigManager",id:"configmanager",level:3}];function d(n){const e={a:"a",code:"code",em:"em",h1:"h1",h2:"h2",h3:"h3",header:"header",li:"li",p:"p",pre:"pre",strong:"strong",ul:"ul",...(0,o.R)(),...n.components};return(0,s.jsxs)(s.Fragment,{children:[(0,s.jsx)(e.header,{children:(0,s.jsx)(e.h1,{id:"config_classpy",children:"config_class.py"})}),"\n",(0,s.jsxs)(e.p,{children:[(0,s.jsx)(e.em,{children:"Source"}),": ",(0,s.jsx)(e.a,{href:"https://github.com/sunholo-data/sunholo-py/blob/main/sunholo/utils/config_class.py",children:"sunholo/utils/config_class.py"})]}),"\n",(0,s.jsx)(e.h2,{id:"classes",children:"Classes"}),"\n",(0,s.jsx)(e.h3,{id:"configmanager",children:"ConfigManager"}),"\n",(0,s.jsx)(e.p,{children:"No docstring available."}),"\n",(0,s.jsxs)(e.ul,{children:["\n",(0,s.jsxs)(e.li,{children:[(0,s.jsx)(e.strong,{children:"init"}),"(self, vector_name: str, validate: bool = True)","\n",(0,s.jsxs)(e.ul,{children:["\n",(0,s.jsx)(e.li,{children:"Initialize the ConfigManager with a vector name.\nRequires a local config/ folder holding your configuration files or the env var VAC_CONFIG_FOLDER to be set."}),"\n"]}),"\n"]}),"\n"]}),"\n",(0,s.jsxs)(e.p,{children:["Read more at: ",(0,s.jsx)(e.a,{href:"https://dev.sunholo.com/docs/config",children:"https://dev.sunholo.com/docs/config"})]}),"\n",(0,s.jsx)(e.p,{children:"Args:\nvector_name (str): The name of the vector in the configuration files.\nvalidate (bool): Whether to validate the configurations"}),"\n",(0,s.jsx)(e.p,{children:"Example:"}),"\n",(0,s.jsx)(e.pre,{children:(0,s.jsx)(e.code,{className:"language-python",children:'# Usage example:\nconfig = ConfigManager("my_vac")\nagent = config.vacConfig("agent")\n'})}),"\n",(0,s.jsxs)(e.ul,{children:["\n",(0,s.jsxs)(e.li,{children:["\n",(0,s.jsx)(e.p,{children:"_check_and_reload_configs(self)"}),"\n",(0,s.jsxs)(e.ul,{children:["\n",(0,s.jsx)(e.li,{children:"Check if configurations are older than 5 minutes and reload if necessary."}),"\n"]}),"\n"]}),"\n",(0,s.jsxs)(e.li,{children:["\n",(0,s.jsx)(e.p,{children:"_load_configs_from_folder(self, folder)"}),"\n",(0,s.jsxs)(e.ul,{children:["\n",(0,s.jsx)(e.li,{children:"Load all configuration files from a specific folder into a dictionary."}),"\n"]}),"\n"]}),"\n"]}),"\n",(0,s.jsx)(e.p,{children:"Args:\nfolder (str): The path of the folder to load configurations from."}),"\n",(0,s.jsx)(e.p,{children:"Returns:\ndict: A dictionary of configurations grouped by their 'kind' key."}),"\n",(0,s.jsxs)(e.ul,{children:["\n",(0,s.jsxs)(e.li,{children:["_merge_dicts(self, dict1, dict2)","\n",(0,s.jsxs)(e.ul,{children:["\n",(0,s.jsx)(e.li,{children:"Recursively merge two dictionaries. Local values in dict2 will overwrite global values in dict1."}),"\n"]}),"\n"]}),"\n"]}),"\n",(0,s.jsx)(e.p,{children:"Args:\ndict1 (dict): The global dictionary.\ndict2 (dict): The local dictionary."}),"\n",(0,s.jsx)(e.p,{children:"Returns:\ndict: The merged dictionary."}),"\n",(0,s.jsxs)(e.ul,{children:["\n",(0,s.jsxs)(e.li,{children:["_reload_config_file(self, config_file, filename, is_local=False)","\n",(0,s.jsxs)(e.ul,{children:["\n",(0,s.jsx)(e.li,{children:"Helper function to load a config file and update the cache."}),"\n"]}),"\n"]}),"\n"]}),"\n",(0,s.jsx)(e.p,{children:"Args:\nconfig_file (str): The path to the configuration file.\nfilename (str): The name of the configuration file.\nis_local (bool): Indicates if the config file is from the local folder."}),"\n",(0,s.jsx)(e.p,{children:"Returns:\ndict: The loaded configuration."}),"\n",(0,s.jsxs)(e.ul,{children:["\n",(0,s.jsxs)(e.li,{children:["agentConfig(self, key: str)","\n",(0,s.jsxs)(e.ul,{children:["\n",(0,s.jsx)(e.li,{children:"Fetch a key from 'agentConfig' kind configuration."}),"\n"]}),"\n"]}),"\n"]}),"\n",(0,s.jsx)(e.p,{children:"Args:\nkey (str): The key to fetch from the configuration."}),"\n",(0,s.jsx)(e.p,{children:"Returns:\nstr: The value associated with the specified key."}),"\n",(0,s.jsxs)(e.ul,{children:["\n",(0,s.jsxs)(e.li,{children:["load_all_configs(self)","\n",(0,s.jsxs)(e.ul,{children:["\n",(0,s.jsx)(e.li,{children:"Load all configuration files from the specified directories into a dictionary.\nCaching is used to avoid reloading files within a 5-minute window."}),"\n"]}),"\n"]}),"\n"]}),"\n",(0,s.jsx)(e.p,{children:"Returns:\ndict: A dictionary of configurations grouped by their 'kind' key."}),"\n",(0,s.jsxs)(e.ul,{children:["\n",(0,s.jsxs)(e.li,{children:["promptConfig(self, key: str)","\n",(0,s.jsxs)(e.ul,{children:["\n",(0,s.jsx)(e.li,{children:"Fetch a key from 'promptConfig' kind configuration."}),"\n"]}),"\n"]}),"\n"]}),"\n",(0,s.jsx)(e.p,{children:"Args:\nkey (str): The key to fetch from the configuration."}),"\n",(0,s.jsx)(e.p,{children:"Returns:\nstr: The value associated with the specified key."}),"\n",(0,s.jsxs)(e.ul,{children:["\n",(0,s.jsxs)(e.li,{children:["vacConfig(self, key: str)","\n",(0,s.jsxs)(e.ul,{children:["\n",(0,s.jsx)(e.li,{children:"Fetch a key from 'vacConfig' kind configuration."}),"\n"]}),"\n"]}),"\n"]}),"\n",(0,s.jsx)(e.p,{children:"Args:\nkey (str): The key to fetch from the configuration."}),"\n",(0,s.jsx)(e.p,{children:"Returns:\nstr: The value associated with the specified key."})]})}function h(n={}){const{wrapper:e}={...(0,o.R)(),...n.components};return e?(0,s.jsx)(e,{...n,children:(0,s.jsx)(d,{...n})}):d(n)}},8453:(n,e,i)=>{i.d(e,{R:()=>c,x:()=>r});var s=i(6540);const o={},l=s.createContext(o);function c(n){const e=s.useContext(l);return s.useMemo((function(){return"function"==typeof n?n(e):{...e,...n}}),[e,n])}function r(n){let e;return e=n.disableParentContext?"function"==typeof n.components?n.components(o):n.components||o:c(n.components),s.createElement(l.Provider,{value:e},n.children)}}}]);