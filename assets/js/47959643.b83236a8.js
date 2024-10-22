"use strict";(self.webpackChunkdocs=self.webpackChunkdocs||[]).push([[3860],{4659:(e,s,a)=>{a.r(s),a.d(s,{assets:()=>c,contentTitle:()=>r,default:()=>d,frontMatter:()=>o,metadata:()=>i,toc:()=>u});var t=a(4848),n=a(8453);const o={},r="Supabase",i={id:"databases/supabase",title:"Supabase",description:"Supabase is a popular GenAI database that has many great GenAI features build in.",source:"@site/docs/databases/supabase.md",sourceDirName:"databases",slug:"/databases/supabase",permalink:"/docs/databases/supabase",draft:!1,unlisted:!1,editUrl:"https://github.com/sunholo-data/sunholo-py/tree/main/docs/docs/databases/supabase.md",tags:[],version:"current",frontMatter:{},sidebar:"tutorialSidebar",previous:{title:"PostgreSQL databases",permalink:"/docs/databases/postgres"},next:{title:"How To",permalink:"/docs/howto/"}},c={},u=[{value:"Usage",id:"usage",level:2},{value:"Auto-creation of tables",id:"auto-creation-of-tables",level:2}];function l(e){const s={a:"a",code:"code",h1:"h1",h2:"h2",header:"header",li:"li",p:"p",pre:"pre",ul:"ul",...(0,n.R)(),...e.components};return(0,t.jsxs)(t.Fragment,{children:[(0,t.jsx)(s.header,{children:(0,t.jsx)(s.h1,{id:"supabase",children:"Supabase"})}),"\n",(0,t.jsxs)(s.p,{children:[(0,t.jsx)(s.a,{href:"https://supabase.com/",children:"Supabase"})," is a popular GenAI database that has many great GenAI features build in."]}),"\n",(0,t.jsx)(s.h2,{id:"usage",children:"Usage"}),"\n",(0,t.jsx)(s.p,{children:"To start using Supabase, set your configuration to use it as a memory:"}),"\n",(0,t.jsx)(s.pre,{children:(0,t.jsx)(s.code,{className:"language-yaml",children:"    memory:\n      - supabase-vectorstore:\n          vectorstore: supabase\n"})}),"\n",(0,t.jsx)(s.p,{children:"When you create your Supabse account, you will receive these values that need to be added as an environment variable:"}),"\n",(0,t.jsxs)(s.ul,{children:["\n",(0,t.jsx)(s.li,{children:"SUPABASE_URL"}),"\n",(0,t.jsx)(s.li,{children:"SUPABASE_KEY"}),"\n"]}),"\n",(0,t.jsxs)(s.p,{children:["Supabase also requires a ",(0,t.jsx)(s.code,{children:"DB_CONNECTION_STRING"})," environment variable with the connection string to your deployed Supabase instance.\nThis will look something like this:"]}),"\n",(0,t.jsx)(s.p,{children:(0,t.jsx)(s.code,{children:"postgres://postgres.<your-supabase-uri>@aws-0-eu-central-1.pooler.supabase.com:6543/postgres"})}),"\n",(0,t.jsx)(s.h2,{id:"auto-creation-of-tables",children:"Auto-creation of tables"}),"\n",(0,t.jsxs)(s.p,{children:["On first embed, if no table is specified the name of the ",(0,t.jsx)(s.code,{children:"vector_name"}),", it will attempt to setup and create a vector store database, using the ",(0,t.jsx)(s.a,{href:"https://github.com/sunholo-data/sunholo-py/tree/main/sunholo/database/sql/sb",children:"SQL within this github folder"}),"."]})]})}function d(e={}){const{wrapper:s}={...(0,n.R)(),...e.components};return s?(0,t.jsx)(s,{...e,children:(0,t.jsx)(l,{...e})}):l(e)}},8453:(e,s,a)=>{a.d(s,{R:()=>r,x:()=>i});var t=a(6540);const n={},o=t.createContext(n);function r(e){const s=t.useContext(o);return t.useMemo((function(){return"function"==typeof e?e(s):{...s,...e}}),[s,e])}function i(e){let s;return s=e.disableParentContext?"function"==typeof e.components?e.components(n):e.components||n:r(e.components),t.createElement(o.Provider,{value:s},e.children)}}}]);