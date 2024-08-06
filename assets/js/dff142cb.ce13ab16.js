"use strict";(self.webpackChunkdocs=self.webpackChunkdocs||[]).push([[5423],{4505:(e,t,n)=>{n.r(t),n.d(t,{assets:()=>r,contentTitle:()=>d,default:()=>_,frontMatter:()=>s,metadata:()=>i,toc:()=>l});var a=n(4848),o=n(8453);const s={},d="add_file.py",i={id:"sunholo/gcs/add_file",title:"add_file.py",description:"Source: sunholo/gcs/addfile.py",source:"@site/docs/sunholo/gcs/add_file.md",sourceDirName:"sunholo/gcs",slug:"/sunholo/gcs/add_file",permalink:"/docs/sunholo/gcs/add_file",draft:!1,unlisted:!1,editUrl:"https://github.com/sunholo-data/sunholo-py/tree/main/docs/docs/sunholo/gcs/add_file.md",tags:[],version:"current",frontMatter:{},sidebar:"tutorialSidebar",previous:{title:"embed_chunk.py",permalink:"/docs/sunholo/embedder/embed_chunk"},next:{title:"download_url.py",permalink:"/docs/sunholo/gcs/download_url"}},r={},l=[{value:"Functions",id:"functions",level:2},{value:"add_file_to_gcs(filename: str, vector_name: str = None, bucket_name: str = None, metadata: dict = None, bucket_filepath: str = None)",id:"add_file_to_gcsfilename-str-vector_name-str--none-bucket_name-str--none-metadata-dict--none-bucket_filepath-str--none",level:3},{value:"handle_base64_image(base64_data: str, vector_name: str, extension: str)",id:"handle_base64_imagebase64_data-str-vector_name-str-extension-str",level:3},{value:"get_summary_file_name(object_id)",id:"get_summary_file_nameobject_id",level:3},{value:"get_image_file_name(object_id, image_name, mime_type)",id:"get_image_file_nameobject_id-image_name-mime_type",level:3},{value:"get_pdf_split_file_name(object_id, part_name)",id:"get_pdf_split_file_nameobject_id-part_name",level:3},{value:"add_folder_to_gcs(source_folder: str, vector_name: str = None, bucket_name: str = None, metadata: dict = None, bucket_folderpath: str = None)",id:"add_folder_to_gcssource_folder-str-vector_name-str--none-bucket_name-str--none-metadata-dict--none-bucket_folderpath-str--none",level:3},{value:"resolve_bucket(vector_name)",id:"resolve_bucketvector_name",level:3}];function c(e){const t={a:"a",em:"em",h1:"h1",h2:"h2",h3:"h3",p:"p",...(0,o.R)(),...e.components};return(0,a.jsxs)(a.Fragment,{children:[(0,a.jsx)(t.h1,{id:"add_filepy",children:"add_file.py"}),"\n",(0,a.jsxs)(t.p,{children:[(0,a.jsx)(t.em,{children:"Source"}),": ",(0,a.jsx)(t.a,{href:"https://github.com/sunholo-data/sunholo-py/blob/main/sunholo/gcs/add_file.py",children:"sunholo/gcs/add_file.py"})]}),"\n",(0,a.jsx)(t.h2,{id:"functions",children:"Functions"}),"\n",(0,a.jsx)(t.h3,{id:"add_file_to_gcsfilename-str-vector_name-str--none-bucket_name-str--none-metadata-dict--none-bucket_filepath-str--none",children:"add_file_to_gcs(filename: str, vector_name: str = None, bucket_name: str = None, metadata: dict = None, bucket_filepath: str = None)"}),"\n",(0,a.jsx)(t.p,{children:"No docstring available."}),"\n",(0,a.jsx)(t.h3,{id:"handle_base64_imagebase64_data-str-vector_name-str-extension-str",children:"handle_base64_image(base64_data: str, vector_name: str, extension: str)"}),"\n",(0,a.jsx)(t.p,{children:"Handle base64 image data, decode it, save it as a file, upload it to GCS, and return the image URI and MIME type."}),"\n",(0,a.jsx)(t.p,{children:'Args:\nbase64_data (str): The base64 encoded image data.\nvector_name (str): The vector name for the GCS path.\nextension (str): The file extension of the image (e.g., ".jpg", ".png").'}),"\n",(0,a.jsx)(t.p,{children:"Returns:\nTuple[str, str]: The URI of the uploaded image and the MIME type."}),"\n",(0,a.jsx)(t.h3,{id:"get_summary_file_nameobject_id",children:"get_summary_file_name(object_id)"}),"\n",(0,a.jsx)(t.p,{children:"No docstring available."}),"\n",(0,a.jsx)(t.h3,{id:"get_image_file_nameobject_id-image_name-mime_type",children:"get_image_file_name(object_id, image_name, mime_type)"}),"\n",(0,a.jsx)(t.p,{children:"No docstring available."}),"\n",(0,a.jsx)(t.h3,{id:"get_pdf_split_file_nameobject_id-part_name",children:"get_pdf_split_file_name(object_id, part_name)"}),"\n",(0,a.jsx)(t.p,{children:"No docstring available."}),"\n",(0,a.jsx)(t.h3,{id:"add_folder_to_gcssource_folder-str-vector_name-str--none-bucket_name-str--none-metadata-dict--none-bucket_folderpath-str--none",children:"add_folder_to_gcs(source_folder: str, vector_name: str = None, bucket_name: str = None, metadata: dict = None, bucket_folderpath: str = None)"}),"\n",(0,a.jsx)(t.p,{children:"Uploads a folder and all its contents to a specified GCS bucket."}),"\n",(0,a.jsx)(t.h3,{id:"resolve_bucketvector_name",children:"resolve_bucket(vector_name)"}),"\n",(0,a.jsx)(t.p,{children:"No docstring available."})]})}function _(e={}){const{wrapper:t}={...(0,o.R)(),...e.components};return t?(0,a.jsx)(t,{...e,children:(0,a.jsx)(c,{...e})}):c(e)}},8453:(e,t,n)=>{n.d(t,{R:()=>d,x:()=>i});var a=n(6540);const o={},s=a.createContext(o);function d(e){const t=a.useContext(s);return a.useMemo((function(){return"function"==typeof e?e(t):{...t,...e}}),[t,e])}function i(e){let t;return t=e.disableParentContext?"function"==typeof e.components?e.components(o):e.components||o:d(e.components),a.createElement(s.Provider,{value:t},e.children)}}}]);