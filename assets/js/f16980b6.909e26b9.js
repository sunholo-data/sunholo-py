"use strict";(self.webpackChunkdocs=self.webpackChunkdocs||[]).push([[2911],{9667:(e,n,t)=>{t.r(n),t.d(n,{assets:()=>l,contentTitle:()=>s,default:()=>u,frontMatter:()=>o,metadata:()=>c,toc:()=>a});var i=t(4848),r=t(8453);const o={},s="gcp.py",c={id:"sunholo/utils/gcp",title:"gcp.py",description:"Source: sunholo/utils/gcp.py",source:"@site/docs/sunholo/utils/gcp.md",sourceDirName:"sunholo/utils",slug:"/sunholo/utils/gcp",permalink:"/docs/sunholo/utils/gcp",draft:!1,unlisted:!1,editUrl:"https://github.com/sunholo-data/sunholo-py/tree/main/docs/docs/sunholo/utils/gcp.md",tags:[],version:"current",frontMatter:{},sidebar:"tutorialSidebar",previous:{title:"config.py",permalink:"/docs/sunholo/utils/config"},next:{title:"parsers.py",permalink:"/docs/sunholo/utils/parsers"}},l={},a=[{value:"Functions",id:"functions",level:2},{value:"is_running_on_cloudrun()",id:"is_running_on_cloudrun",level:3},{value:"is_running_on_gcp()",id:"is_running_on_gcp",level:3},{value:"get_gcp_project()",id:"get_gcp_project",level:3},{value:"get_env_project_id()",id:"get_env_project_id",level:3},{value:"get_metadata(stem)",id:"get_metadatastem",level:3},{value:"get_region()",id:"get_region",level:3},{value:"get_service_account_email()",id:"get_service_account_email",level:3},{value:"is_gcp_logged_in()",id:"is_gcp_logged_in",level:3}];function d(e){const n={a:"a",code:"code",em:"em",h1:"h1",h2:"h2",h3:"h3",p:"p",pre:"pre",...(0,r.R)(),...e.components};return(0,i.jsxs)(i.Fragment,{children:[(0,i.jsx)(n.h1,{id:"gcppy",children:"gcp.py"}),"\n",(0,i.jsxs)(n.p,{children:[(0,i.jsx)(n.em,{children:"Source"}),": ",(0,i.jsx)(n.a,{href:"https://github.com/sunholo-data/sunholo-py/blob/main/sunholo/utils/gcp.py",children:"sunholo/utils/gcp.py"})]}),"\n",(0,i.jsx)(n.h2,{id:"functions",children:"Functions"}),"\n",(0,i.jsx)(n.h3,{id:"is_running_on_cloudrun",children:"is_running_on_cloudrun()"}),"\n",(0,i.jsx)(n.p,{children:"Check if the current environment is a Google Cloud Run instance."}),"\n",(0,i.jsxs)(n.p,{children:["Returns:\nbool: ",(0,i.jsx)(n.code,{children:"True"})," if running on Cloud Run, ",(0,i.jsx)(n.code,{children:"False"})," otherwise."]}),"\n",(0,i.jsx)(n.p,{children:"Example:"}),"\n",(0,i.jsx)(n.pre,{children:(0,i.jsx)(n.code,{className:"language-python",children:'if is_running_on_cloudrun():\n    print("Running on Cloud Run.")\nelse:\n    print("Not running on Cloud Run.")\n'})}),"\n",(0,i.jsx)(n.h3,{id:"is_running_on_gcp",children:"is_running_on_gcp()"}),"\n",(0,i.jsx)(n.p,{children:"Check if the current environment is a Google Cloud Platform (GCP) instance."}),"\n",(0,i.jsx)(n.p,{children:"This function attempts to reach the GCP metadata server to determine if the code\nis running on a GCP instance."}),"\n",(0,i.jsxs)(n.p,{children:["Returns:\nbool: ",(0,i.jsx)(n.code,{children:"True"})," if running on GCP, ",(0,i.jsx)(n.code,{children:"False"})," otherwise."]}),"\n",(0,i.jsx)(n.p,{children:"Example:"}),"\n",(0,i.jsx)(n.pre,{children:(0,i.jsx)(n.code,{className:"language-python",children:'if is_running_on_gcp():\n    print("Running on GCP.")\nelse:\n    print("Not running on GCP.")\n'})}),"\n",(0,i.jsx)(n.h3,{id:"get_gcp_project",children:"get_gcp_project()"}),"\n",(0,i.jsx)(n.p,{children:"Retrieve the GCP project ID from environment variables or the GCP metadata server."}),"\n",(0,i.jsx)(n.p,{children:"Returns:\nstr or None: The project ID if found, None otherwise."}),"\n",(0,i.jsx)(n.h3,{id:"get_env_project_id",children:"get_env_project_id()"}),"\n",(0,i.jsx)(n.p,{children:"Attempts to retrieve the project ID from environment variables."}),"\n",(0,i.jsx)(n.p,{children:"Returns:\nstr or None: The project ID if found in environment variables, None otherwise."}),"\n",(0,i.jsx)(n.h3,{id:"get_metadatastem",children:"get_metadata(stem)"}),"\n",(0,i.jsx)(n.p,{children:"Retrieve metadata information from the GCP metadata server."}),"\n",(0,i.jsx)(n.p,{children:"Args:\nstem (str): The metadata path to query."}),"\n",(0,i.jsx)(n.p,{children:"Returns:\nstr or None: The metadata information if found, None otherwise."}),"\n",(0,i.jsx)(n.h3,{id:"get_region",children:"get_region()"}),"\n",(0,i.jsx)(n.p,{children:"Retrieve the region of the GCP instance."}),"\n",(0,i.jsx)(n.p,{children:"This function attempts to retrieve the region by extracting it from the zone information\navailable in the GCP metadata server."}),"\n",(0,i.jsx)(n.p,{children:"Returns:\nstr or None: The region if found, None otherwise."}),"\n",(0,i.jsx)(n.h3,{id:"get_service_account_email",children:"get_service_account_email()"}),"\n",(0,i.jsx)(n.p,{children:"Retrieve the service account email from environment variables or the GCP metadata server."}),"\n",(0,i.jsx)(n.p,{children:"Returns:\nstr or None: The service account email if found, None otherwise."}),"\n",(0,i.jsx)(n.h3,{id:"is_gcp_logged_in",children:"is_gcp_logged_in()"}),"\n",(0,i.jsx)(n.p,{children:"Check if the current environment has valid Google Cloud Platform (GCP) credentials."}),"\n",(0,i.jsxs)(n.p,{children:["This function attempts to obtain the default application credentials from the environment.\nIt will return ",(0,i.jsx)(n.code,{children:"True"})," if credentials are available, otherwise it returns ",(0,i.jsx)(n.code,{children:"False"}),"."]}),"\n",(0,i.jsxs)(n.p,{children:["Returns:\nbool: ",(0,i.jsx)(n.code,{children:"True"})," if GCP credentials are available, ",(0,i.jsx)(n.code,{children:"False"})," otherwise."]}),"\n",(0,i.jsx)(n.p,{children:"Example:"}),"\n",(0,i.jsx)(n.pre,{children:(0,i.jsx)(n.code,{className:"language-python",children:'if is_gcp_logged_in():\n    print("GCP credentials found.")\nelse:\n    print("GCP credentials not found or invalid.")\n'})})]})}function u(e={}){const{wrapper:n}={...(0,r.R)(),...e.components};return n?(0,i.jsx)(n,{...e,children:(0,i.jsx)(d,{...e})}):d(e)}},8453:(e,n,t)=>{t.d(n,{R:()=>s,x:()=>c});var i=t(6540);const r={},o=i.createContext(r);function s(e){const n=i.useContext(o);return i.useMemo((function(){return"function"==typeof e?e(n):{...n,...e}}),[n,e])}function c(e){let n;return n=e.disableParentContext?"function"==typeof e.components?e.components(r):e.components||r:s(e.components),i.createElement(o.Provider,{value:n},e.children)}}}]);