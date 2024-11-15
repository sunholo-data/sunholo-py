"use strict";(self.webpackChunkdocs=self.webpackChunkdocs||[]).push([[5216],{6080:(e,n,t)=>{t.r(n),t.d(n,{assets:()=>c,contentTitle:()=>i,default:()=>l,frontMatter:()=>s,metadata:()=>a,toc:()=>u});var o=t(4848),r=t(8453);const s={},i="event_grid.py",a={id:"sunholo/azure/event_grid",title:"event_grid.py",description:"Source: sunholo/azure/eventgrid.py",source:"@site/docs/sunholo/azure/event_grid.md",sourceDirName:"sunholo/azure",slug:"/sunholo/azure/event_grid",permalink:"/docs/sunholo/azure/event_grid",draft:!1,unlisted:!1,editUrl:"https://github.com/sunholo-data/sunholo-py/tree/main/docs/docs/sunholo/azure/event_grid.md",tags:[],version:"current",frontMatter:{},sidebar:"tutorialSidebar",previous:{title:"blobs.py",permalink:"/docs/sunholo/azure/blobs"},next:{title:"discord.py",permalink:"/docs/sunholo/bots/discord"}},c={},u=[{value:"Functions",id:"functions",level:2},{value:"process_azure_blob_event(events: list) -&gt; tuple",id:"process_azure_blob_eventevents-list---tuple",level:3}];function d(e){const n={a:"a",code:"code",em:"em",h1:"h1",h2:"h2",h3:"h3",header:"header",p:"p",pre:"pre",...(0,r.R)(),...e.components};return(0,o.jsxs)(o.Fragment,{children:[(0,o.jsx)(n.header,{children:(0,o.jsx)(n.h1,{id:"event_gridpy",children:"event_grid.py"})}),"\n",(0,o.jsxs)(n.p,{children:[(0,o.jsx)(n.em,{children:"Source"}),": ",(0,o.jsx)(n.a,{href:"https://github.com/sunholo-data/sunholo-py/blob/main/sunholo/azure/event_grid.py",children:"sunholo/azure/event_grid.py"})]}),"\n",(0,o.jsx)(n.h2,{id:"functions",children:"Functions"}),"\n",(0,o.jsx)(n.h3,{id:"process_azure_blob_eventevents-list---tuple",children:"process_azure_blob_event(events: list) -> tuple"}),"\n",(0,o.jsx)(n.p,{children:"Extracts message data and metadata from an Azure Blob Storage event."}),"\n",(0,o.jsx)(n.p,{children:"Args:\nevents (list): The list of Azure Event Grid event data."}),"\n",(0,o.jsx)(n.p,{children:"Returns:\ntuple: A tuple containing the blob URL, attributes as metadata, and the vector name."}),"\n",(0,o.jsx)(n.p,{children:"Example of Event Grid schema:"}),"\n",(0,o.jsx)(n.pre,{children:(0,o.jsx)(n.code,{children:'{\n    "topic": "/subscriptions/subscription-id/resourceGroups/resource-group/providers/Microsoft.Storage/storageAccounts/storage-account",\n    "subject": "/blobServices/default/containers/container/blobs/blob",\n    "eventType": "Microsoft.Storage.BlobCreated",\n    "eventTime": "2021-01-01T12:34:56.789Z",\n    "id": "event-id",\n    "data": {\n        "api": "PutBlob",\n        "clientRequestId": "client-request-id",\n        "requestId": "request-id",\n        "eTag": "etag",\n        "contentType": "application/octet-stream",\n        "contentLength": 524288,\n        "blobType": "BlockBlob",\n        "url": "https://storage-account.blob.core.windows.net/container/blob",\n        "sequencer": "0000000000000000000000000",\n        "storageDiagnostics": {\n            "batchId": "batch-id"\n        }\n    },\n    "dataVersion": "",\n    "metadataVersion": "1"\n}\n'})})]})}function l(e={}){const{wrapper:n}={...(0,r.R)(),...e.components};return n?(0,o.jsx)(n,{...e,children:(0,o.jsx)(d,{...e})}):d(e)}},8453:(e,n,t)=>{t.d(n,{R:()=>i,x:()=>a});var o=t(6540);const r={},s=o.createContext(r);function i(e){const n=o.useContext(s);return o.useMemo((function(){return"function"==typeof e?e(n):{...n,...e}}),[n,e])}function a(e){let n;return n=e.disableParentContext?"function"==typeof e.components?e.components(r):e.components||r:i(e.components),o.createElement(s.Provider,{value:n},e.children)}}}]);