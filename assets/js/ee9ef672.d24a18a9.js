"use strict";(self.webpackChunkdocs=self.webpackChunkdocs||[]).push([[892],{1604:(e,t,n)=>{n.r(t),n.d(t,{assets:()=>l,contentTitle:()=>r,default:()=>h,frontMatter:()=>s,metadata:()=>o,toc:()=>c});var a=n(4848),i=n(8453);const s={},r="Pirate Talk",o={id:"VACs/pirate_talk",title:"Pirate Talk",description:"This VAC is a 'hello world' Langserve app that is taken from the official piratetalk Langserve template.",source:"@site/docs/VACs/pirate_talk.md",sourceDirName:"VACs",slug:"/VACs/pirate_talk",permalink:"/docs/VACs/pirate_talk",draft:!1,unlisted:!1,editUrl:"https://github.com/sunholo-data/sunholo-py/tree/main/docs/docs/VACs/pirate_talk.md",tags:[],version:"current",frontMatter:{},sidebar:"tutorialSidebar",previous:{title:"Introduction",permalink:"/docs/"},next:{title:"Config files",permalink:"/docs/config"}},l={},c=[{value:"Summary",id:"summary",level:2},{value:"Config yaml",id:"config-yaml",level:2}];function d(e){const t={a:"a",code:"code",h1:"h1",h2:"h2",img:"img",li:"li",p:"p",pre:"pre",ul:"ul",...(0,i.R)(),...e.components};return(0,a.jsxs)(a.Fragment,{children:[(0,a.jsx)(t.h1,{id:"pirate-talk",children:"Pirate Talk"}),"\n",(0,a.jsxs)(t.p,{children:["This VAC is a 'hello world' Langserve app that is taken from the official ",(0,a.jsx)(t.a,{href:"https://templates.langchain.com/?integration_name=pirate-speak",children:"pirate_talk Langserve template"}),"."]}),"\n",(0,a.jsx)(t.p,{children:"It demonstrates how to deploy a Langserve application on Multivac, and the configuration needed.  Its a good starter VAC to try first."}),"\n",(0,a.jsx)(t.h2,{id:"summary",children:"Summary"}),"\n",(0,a.jsx)(t.p,{children:"This VAC application translates your questions into pirate speak! Ohh arr."}),"\n",(0,a.jsx)(t.p,{children:(0,a.jsx)(t.img,{src:n(3935).A+"",width:"1376",height:"948"})}),"\n",(0,a.jsx)(t.h2,{id:"config-yaml",children:"Config yaml"}),"\n",(0,a.jsx)(t.p,{children:"An explanation of the configuration is below:"}),"\n",(0,a.jsxs)(t.ul,{children:["\n",(0,a.jsxs)(t.li,{children:[(0,a.jsx)(t.code,{children:"vac.pirate_speak"}),' - this is the key that all other configurations are derived from, referred to as "vector_name"']}),"\n",(0,a.jsxs)(t.li,{children:[(0,a.jsx)(t.code,{children:"llm"}),": The configuration specifies an LLM model.  You can swap this for any model supported by ",(0,a.jsx)(t.code,{children:"sunholo"})," so that it can work with the ",(0,a.jsx)(t.code,{children:"pick_llm()"})," function via ",(0,a.jsx)(t.code,{children:'model = pick_llm("pirate_speak")'}),"."]}),"\n",(0,a.jsxs)(t.li,{children:[(0,a.jsx)(t.code,{children:"agent"}),": Required to specify what type of agent this VAC is, which determines which Cloud Run or other runtime is queried via the endpoints"]}),"\n",(0,a.jsxs)(t.li,{children:[(0,a.jsx)(t.code,{children:"display_name"}),": Used by end clients such as the webapp for the UI."]}),"\n",(0,a.jsxs)(t.li,{children:[(0,a.jsx)(t.code,{children:"avatar_url"}),": Used by end clients such as the webapp for the UI."]}),"\n",(0,a.jsxs)(t.li,{children:[(0,a.jsx)(t.code,{children:"description"}),": Used by end clients such as the webapp for the UI."]}),"\n",(0,a.jsxs)(t.li,{children:[(0,a.jsx)(t.code,{children:"tags"}),": Used to specify which users are authorized to see this VAC, defined via ",(0,a.jsx)(t.code,{children:"users_config.yaml"})]}),"\n"]}),"\n",(0,a.jsx)(t.pre,{children:(0,a.jsx)(t.code,{className:"language-yaml",children:'kind: vacConfig\napiVersion: v1\nvac:\n    pirate_speak:\n        llm: openai\n        agent: langserve\n        #agent_url: you can specify manually your URL endpoint here, or on Multivac it will be populated automatically\n        display_name: Pirate Speak\n        tags: ["free"] # for user access, matches users_config.yaml\n        avatar_url: https://avatars.githubusercontent.com/u/126733545?s=48&v=4\n        description: A Langserve demo using a demo [Langchain Template](https://templates.langchain.com/) that will repeat back what you say but in a pirate accent.  Ooh argh me hearties!  Langchain templates cover many different GenAI use cases and all can be streamed to Multivac clients.\n'})})]})}function h(e={}){const{wrapper:t}={...(0,i.R)(),...e.components};return t?(0,a.jsx)(t,{...e,children:(0,a.jsx)(d,{...e})}):d(e)}},3935:(e,t,n)=>{n.d(t,{A:()=>a});const a=n.p+"assets/images/vac-pirate-speak-d81a9474af9df325006a4227218a109c.png"},8453:(e,t,n)=>{n.d(t,{R:()=>r,x:()=>o});var a=n(6540);const i={},s=a.createContext(i);function r(e){const t=a.useContext(s);return a.useMemo((function(){return"function"==typeof e?e(t):{...t,...e}}),[t,e])}function o(e){let t;return t=e.disableParentContext?"function"==typeof e.components?e.components(i):e.components||i:r(e.components),a.createElement(s.Provider,{value:t},e.children)}}}]);