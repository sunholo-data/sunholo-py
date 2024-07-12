"use strict";(self.webpackChunkdocs=self.webpackChunkdocs||[]).push([[670],{1277:(e,t,s)=>{s.r(t),s.d(t,{assets:()=>i,contentTitle:()=>l,default:()=>d,frontMatter:()=>o,metadata:()=>c,toc:()=>u});var r=s(4848),n=s(8453);const o={},l="download_url.py",c={id:"sunholo/gcs/download_url",title:"download_url.py",description:"Source: sunholo/gcs/downloadurl.py",source:"@site/docs/sunholo/gcs/download_url.md",sourceDirName:"sunholo/gcs",slug:"/sunholo/gcs/download_url",permalink:"/docs/sunholo/gcs/download_url",draft:!1,unlisted:!1,editUrl:"https://github.com/sunholo-data/sunholo-py/tree/main/docs/docs/sunholo/gcs/download_url.md",tags:[],version:"current",frontMatter:{},sidebar:"tutorialSidebar",previous:{title:"add_file.py",permalink:"/docs/sunholo/gcs/add_file"},next:{title:"metadata.py",permalink:"/docs/sunholo/gcs/metadata"}},i={},u=[{value:"Functions",id:"functions",level:2},{value:"construct_download_link(source_uri: str) -&gt; tuple[str, str, bool]",id:"construct_download_linksource_uri-str---tuplestr-str-bool",level:3},{value:"get_bytes_from_gcs(gs_uri)",id:"get_bytes_from_gcsgs_uri",level:3},{value:"get_image_from_gcs(gs_uri: str)",id:"get_image_from_gcsgs_uri-str",level:3},{value:"construct_download_link_simple(bucket_name: str, object_name: str) -&gt; tuple[str, str, bool]",id:"construct_download_link_simplebucket_name-str-object_name-str---tuplestr-str-bool",level:3},{value:"get_bucket(bucket_name)",id:"get_bucketbucket_name",level:3},{value:"parse_gs_uri(gs_uri: str) -&gt; tuple[str, str]",id:"parse_gs_urigs_uri-str---tuplestr-str",level:3},{value:"sign_gcs_url(bucket_name: str, object_name: str, expiry_secs=86400)",id:"sign_gcs_urlbucket_name-str-object_name-str-expiry_secs86400",level:3}];function a(e){const t={a:"a",em:"em",h1:"h1",h2:"h2",h3:"h3",p:"p",...(0,n.R)(),...e.components};return(0,r.jsxs)(r.Fragment,{children:[(0,r.jsx)(t.h1,{id:"download_urlpy",children:"download_url.py"}),"\n",(0,r.jsxs)(t.p,{children:[(0,r.jsx)(t.em,{children:"Source"}),": ",(0,r.jsx)(t.a,{href:"https://github.com/sunholo-data/sunholo-py/blob/main/sunholo/gcs/download_url.py",children:"sunholo/gcs/download_url.py"})]}),"\n",(0,r.jsx)(t.h2,{id:"functions",children:"Functions"}),"\n",(0,r.jsx)(t.h3,{id:"construct_download_linksource_uri-str---tuplestr-str-bool",children:"construct_download_link(source_uri: str) -> tuple[str, str, bool]"}),"\n",(0,r.jsx)(t.p,{children:"Creates a viewable Cloud Storage web browser link from a gs:// URI."}),"\n",(0,r.jsx)(t.h3,{id:"get_bytes_from_gcsgs_uri",children:"get_bytes_from_gcs(gs_uri)"}),"\n",(0,r.jsx)(t.p,{children:"Downloads a file from Google Cloud Storage and returns its bytes."}),"\n",(0,r.jsx)(t.p,{children:"Args:\ngs_uri (str): The Google Cloud Storage URI of the file to download (e.g., 'gs://bucket_name/file_name')."}),"\n",(0,r.jsx)(t.p,{children:"Returns:\nbytes: The content of the file in bytes, or None if an error occurs."}),"\n",(0,r.jsx)(t.h3,{id:"get_image_from_gcsgs_uri-str",children:"get_image_from_gcs(gs_uri: str)"}),"\n",(0,r.jsx)(t.p,{children:"Converts image bytes from GCS to a PIL Image object."}),"\n",(0,r.jsx)(t.h3,{id:"construct_download_link_simplebucket_name-str-object_name-str---tuplestr-str-bool",children:"construct_download_link_simple(bucket_name: str, object_name: str) -> tuple[str, str, bool]"}),"\n",(0,r.jsx)(t.p,{children:"Creates a viewable Cloud Storage web browser link from a gs:// URI."}),"\n",(0,r.jsx)(t.p,{children:"Args:\nsource_uri: The gs:// URI of the object in Cloud Storage."}),"\n",(0,r.jsx)(t.p,{children:"Returns:\nA URL that directly access the object in the Cloud Storage web browser."}),"\n",(0,r.jsx)(t.h3,{id:"get_bucketbucket_name",children:"get_bucket(bucket_name)"}),"\n",(0,r.jsx)(t.p,{children:"No docstring available."}),"\n",(0,r.jsx)(t.h3,{id:"parse_gs_urigs_uri-str---tuplestr-str",children:"parse_gs_uri(gs_uri: str) -> tuple[str, str]"}),"\n",(0,r.jsx)(t.p,{children:"Parses a gs:// URI into the bucket name and object name."}),"\n",(0,r.jsx)(t.p,{children:"Args:\ngs_uri: The gs:// URI to parse."}),"\n",(0,r.jsx)(t.p,{children:"Returns:\nA tuple containing the bucket name and object name."}),"\n",(0,r.jsx)(t.h3,{id:"sign_gcs_urlbucket_name-str-object_name-str-expiry_secs86400",children:"sign_gcs_url(bucket_name: str, object_name: str, expiry_secs=86400)"}),"\n",(0,r.jsx)(t.p,{children:"No docstring available."})]})}function d(e={}){const{wrapper:t}={...(0,n.R)(),...e.components};return t?(0,r.jsx)(t,{...e,children:(0,r.jsx)(a,{...e})}):a(e)}},8453:(e,t,s)=>{s.d(t,{R:()=>l,x:()=>c});var r=s(6540);const n={},o=r.createContext(n);function l(e){const t=r.useContext(o);return r.useMemo((function(){return"function"==typeof e?e(t):{...t,...e}}),[t,e])}function c(e){let t;return t=e.disableParentContext?"function"==typeof e.components?e.components(n):e.components||n:l(e.components),r.createElement(o.Provider,{value:t},e.children)}}}]);