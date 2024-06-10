"use strict";(self.webpackChunkdocs=self.webpackChunkdocs||[]).push([[2851],{1687:(e,n,o)=>{o.r(n),o.d(n,{assets:()=>l,contentTitle:()=>i,default:()=>a,frontMatter:()=>s,metadata:()=>c,toc:()=>u});var r=o(4848),t=o(8453);const s={},i="memory_tools.py",c={id:"sunholo/vertex/memory_tools",title:"memory_tools.py",description:"Source: sunholo/vertex/memorytools.py",source:"@site/docs/sunholo/vertex/memory_tools.md",sourceDirName:"sunholo/vertex",slug:"/sunholo/vertex/memory_tools",permalink:"/docs/sunholo/vertex/memory_tools",draft:!1,unlisted:!1,editUrl:"https://github.com/sunholo-data/sunholo-py/tree/main/docs/docs/sunholo/vertex/memory_tools.md",tags:[],version:"current",frontMatter:{},sidebar:"tutorialSidebar",previous:{title:"init.py",permalink:"/docs/sunholo/vertex/init"},next:{title:"safety.py",permalink:"/docs/sunholo/vertex/safety"}},l={},u=[{value:"Functions",id:"functions",level:2},{value:"get_vertex_memories(vector_name)",id:"get_vertex_memoriesvector_name",level:3},{value:"print_grounding_response(response)",id:"print_grounding_responseresponse",level:3}];function d(e){const n={a:"a",code:"code",em:"em",h1:"h1",h2:"h2",h3:"h3",li:"li",p:"p",pre:"pre",ul:"ul",...(0,t.R)(),...e.components};return(0,r.jsxs)(r.Fragment,{children:[(0,r.jsx)(n.h1,{id:"memory_toolspy",children:"memory_tools.py"}),"\n",(0,r.jsxs)(n.p,{children:[(0,r.jsx)(n.em,{children:"Source"}),": ",(0,r.jsx)(n.a,{href:"https://github.com/sunholo-data/sunholo-py/blob/main/sunholo/vertex/memory_tools.py",children:"sunholo/vertex/memory_tools.py"})]}),"\n",(0,r.jsx)(n.h2,{id:"functions",children:"Functions"}),"\n",(0,r.jsx)(n.h3,{id:"get_vertex_memoriesvector_name",children:"get_vertex_memories(vector_name)"}),"\n",(0,r.jsx)(n.p,{children:"Retrieves a LlamaIndex corpus from Vertex AI based on the provided Google Cloud configuration."}),"\n",(0,r.jsx)(n.p,{children:"This function constructs a corpus name using project details from the configuration and attempts\nto fetch the corresponding corpus. If the corpus cannot be retrieved, it raises an error."}),"\n",(0,r.jsx)(n.p,{children:"Parameters:"}),"\n",(0,r.jsxs)(n.ul,{children:["\n",(0,r.jsx)(n.li,{children:"vector_name: The name of the of VAC"}),"\n"]}),"\n",(0,r.jsx)(n.p,{children:"Returns:"}),"\n",(0,r.jsxs)(n.ul,{children:["\n",(0,r.jsx)(n.li,{children:"List of corpus objects fetched from Vertex AI."}),"\n"]}),"\n",(0,r.jsx)(n.p,{children:"Raises:"}),"\n",(0,r.jsxs)(n.ul,{children:["\n",(0,r.jsx)(n.li,{children:"ValueError: If any of the required configurations (project_id, location, or rag_id) are missing,\nor if the corpus cannot be retrieved."}),"\n"]}),"\n",(0,r.jsx)(n.p,{children:"Example:"}),"\n",(0,r.jsx)(n.pre,{children:(0,r.jsx)(n.code,{className:"language-python",children:'\n# Fetch the corpus\ntry:\n    corpus = get_corpus("edmonbrain")\n    print("Corpus fetched successfully:", corpus)\nexcept ValueError as e:\n    print("Error fetching corpus:", str(e))\n'})}),"\n",(0,r.jsx)(n.h3,{id:"print_grounding_responseresponse",children:"print_grounding_response(response)"}),"\n",(0,r.jsx)(n.p,{children:"Prints Gemini response with grounding citations."})]})}function a(e={}){const{wrapper:n}={...(0,t.R)(),...e.components};return n?(0,r.jsx)(n,{...e,children:(0,r.jsx)(d,{...e})}):d(e)}},8453:(e,n,o)=>{o.d(n,{R:()=>i,x:()=>c});var r=o(6540);const t={},s=r.createContext(t);function i(e){const n=r.useContext(s);return r.useMemo((function(){return"function"==typeof e?e(n):{...n,...e}}),[n,e])}function c(e){let n;return n=e.disableParentContext?"function"==typeof e.components?e.components(t):e.components||t:i(e.components),r.createElement(s.Provider,{value:n},e.children)}}}]);