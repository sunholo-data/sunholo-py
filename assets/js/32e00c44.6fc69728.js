"use strict";(self.webpackChunkdocs=self.webpackChunkdocs||[]).push([[3516],{2494:(e,n,l)=>{l.r(n),l.d(n,{assets:()=>o,contentTitle:()=>t,default:()=>h,frontMatter:()=>i,metadata:()=>d,toc:()=>a});var s=l(4848),r=l(8453);const i={},t="loaders.py",d={id:"sunholo/chunker/loaders",title:"loaders.py",description:"Source: sunholo/chunker/loaders.py",source:"@site/docs/sunholo/chunker/loaders.md",sourceDirName:"sunholo/chunker",slug:"/sunholo/chunker/loaders",permalink:"/docs/sunholo/chunker/loaders",draft:!1,unlisted:!1,editUrl:"https://github.com/sunholo-data/sunholo-py/tree/main/docs/docs/sunholo/chunker/loaders.md",tags:[],version:"current",frontMatter:{},sidebar:"tutorialSidebar",previous:{title:"images.py",permalink:"/docs/sunholo/chunker/images"},next:{title:"message_data.py",permalink:"/docs/sunholo/chunker/message_data"}},o={},a=[{value:"Functions",id:"functions",level:2},{value:"convert_to_txt(file_path)",id:"convert_to_txtfile_path",level:3},{value:"convert_to_txt_and_extract(gs_file, split=False)",id:"convert_to_txt_and_extractgs_file-splitfalse",level:3},{value:"ignore_files(filepath)",id:"ignore_filesfilepath",level:3},{value:"read_file_to_documents(gs_file: pathlib.Path, metadata: dict = None)",id:"read_file_to_documentsgs_file-pathlibpath-metadata-dict--none",level:3},{value:"read_gdrive_to_document(url: str, metadata: dict = None)",id:"read_gdrive_to_documenturl-str-metadata-dict--none",level:3},{value:"read_git_repo(clone_url, branch=&#39;main&#39;, metadata=None)",id:"read_git_repoclone_url-branchmain-metadatanone",level:3},{value:"read_url_to_document(url: str, metadata: dict = None)",id:"read_url_to_documenturl-str-metadata-dict--none",level:3},{value:"Classes",id:"classes",level:2},{value:"MyGoogleDriveLoader",id:"mygoogledriveloader",level:3},{value:"Notes",id:"notes",level:2}];function c(e){const n={a:"a",code:"code",em:"em",h1:"h1",h2:"h2",h3:"h3",li:"li",ol:"ol",p:"p",strong:"strong",ul:"ul",...(0,r.R)(),...e.components};return(0,s.jsxs)(s.Fragment,{children:[(0,s.jsx)(n.h1,{id:"loaderspy",children:"loaders.py"}),"\n",(0,s.jsxs)(n.p,{children:[(0,s.jsx)(n.em,{children:"Source"}),": ",(0,s.jsx)(n.a,{href:"https://github.com/sunholo-data/sunholo-py/blob/main/sunholo/chunker/loaders.py",children:"sunholo/chunker/loaders.py"})]}),"\n",(0,s.jsx)(n.h2,{id:"functions",children:"Functions"}),"\n",(0,s.jsx)(n.h3,{id:"convert_to_txtfile_path",children:"convert_to_txt(file_path)"}),"\n",(0,s.jsx)(n.p,{children:"No docstring available."}),"\n",(0,s.jsx)(n.h3,{id:"convert_to_txt_and_extractgs_file-splitfalse",children:"convert_to_txt_and_extract(gs_file, split=False)"}),"\n",(0,s.jsx)(n.p,{children:"No docstring available."}),"\n",(0,s.jsx)(n.h3,{id:"ignore_filesfilepath",children:"ignore_files(filepath)"}),"\n",(0,s.jsx)(n.p,{children:'Returns True if the given path\'s file extension is found within\nconfig.json "code_extensions" array\nReturns False if not'}),"\n",(0,s.jsx)(n.h3,{id:"read_file_to_documentsgs_file-pathlibpath-metadata-dict--none",children:"read_file_to_documents(gs_file: pathlib.Path, metadata: dict = None)"}),"\n",(0,s.jsx)(n.p,{children:"No docstring available."}),"\n",(0,s.jsx)(n.h3,{id:"read_gdrive_to_documenturl-str-metadata-dict--none",children:"read_gdrive_to_document(url: str, metadata: dict = None)"}),"\n",(0,s.jsx)(n.p,{children:"No docstring available."}),"\n",(0,s.jsx)(n.h3,{id:"read_git_repoclone_url-branchmain-metadatanone",children:"read_git_repo(clone_url, branch='main', metadata=None)"}),"\n",(0,s.jsx)(n.p,{children:"No docstring available."}),"\n",(0,s.jsx)(n.h3,{id:"read_url_to_documenturl-str-metadata-dict--none",children:"read_url_to_document(url: str, metadata: dict = None)"}),"\n",(0,s.jsx)(n.p,{children:"No docstring available."}),"\n",(0,s.jsx)(n.h2,{id:"classes",children:"Classes"}),"\n",(0,s.jsx)(n.h3,{id:"mygoogledriveloader",children:"MyGoogleDriveLoader"}),"\n",(0,s.jsxs)(n.p,{children:["[",(0,s.jsx)(n.em,{children:"Deprecated"}),"] Load Google Docs from ",(0,s.jsx)(n.code,{children:"Google Drive"}),"."]}),"\n",(0,s.jsx)(n.h2,{id:"notes",children:"Notes"}),"\n",(0,s.jsx)(n.p,{children:".. deprecated:: 0.0.32"}),"\n",(0,s.jsxs)(n.ul,{children:["\n",(0,s.jsxs)(n.li,{children:["\n",(0,s.jsxs)(n.p,{children:[(0,s.jsx)(n.strong,{children:"eq"}),"(self, other: Any) -> bool"]}),"\n",(0,s.jsxs)(n.ul,{children:["\n",(0,s.jsx)(n.li,{children:"Return self==value."}),"\n"]}),"\n"]}),"\n",(0,s.jsxs)(n.li,{children:["\n",(0,s.jsxs)(n.p,{children:[(0,s.jsx)(n.strong,{children:"getstate"}),"(self) -> 'DictAny'"]}),"\n",(0,s.jsxs)(n.ul,{children:["\n",(0,s.jsx)(n.li,{children:"Helper for pickle."}),"\n"]}),"\n"]}),"\n",(0,s.jsxs)(n.li,{children:["\n",(0,s.jsxs)(n.p,{children:[(0,s.jsx)(n.strong,{children:"init"}),"(self, url, *args, **kwargs)"]}),"\n",(0,s.jsxs)(n.ul,{children:["\n",(0,s.jsx)(n.li,{children:"Create a new model by parsing and validating input data from keyword arguments."}),"\n"]}),"\n"]}),"\n"]}),"\n",(0,s.jsx)(n.p,{children:"Raises ValidationError if the input data cannot be parsed to form a valid model."}),"\n",(0,s.jsxs)(n.ul,{children:["\n",(0,s.jsxs)(n.li,{children:["\n",(0,s.jsxs)(n.p,{children:[(0,s.jsx)(n.strong,{children:"iter"}),"(self) -> 'TupleGenerator'"]}),"\n",(0,s.jsxs)(n.ul,{children:["\n",(0,s.jsxs)(n.li,{children:["so ",(0,s.jsx)(n.code,{children:"dict(model)"})," works"]}),"\n"]}),"\n"]}),"\n",(0,s.jsxs)(n.li,{children:["\n",(0,s.jsxs)(n.p,{children:[(0,s.jsx)(n.strong,{children:"json_encoder"}),"(obj: Any) -> Any"]}),"\n",(0,s.jsxs)(n.ul,{children:["\n",(0,s.jsx)(n.li,{children:"No docstring available."}),"\n"]}),"\n"]}),"\n",(0,s.jsxs)(n.li,{children:["\n",(0,s.jsxs)(n.p,{children:[(0,s.jsx)(n.strong,{children:"pretty"}),"(self, fmt: Callable[[Any], Any], **kwargs: Any) -> Generator[Any, NoneType, NoneType]"]}),"\n",(0,s.jsxs)(n.ul,{children:["\n",(0,s.jsxs)(n.li,{children:["Used by devtools (",(0,s.jsx)(n.a,{href:"https://python-devtools.helpmanual.io/",children:"https://python-devtools.helpmanual.io/"}),") to provide a human readable representations of objects"]}),"\n"]}),"\n"]}),"\n",(0,s.jsxs)(n.li,{children:["\n",(0,s.jsxs)(n.p,{children:[(0,s.jsx)(n.strong,{children:"repr"}),"(self) -> str"]}),"\n",(0,s.jsxs)(n.ul,{children:["\n",(0,s.jsx)(n.li,{children:"Return repr(self)."}),"\n"]}),"\n"]}),"\n",(0,s.jsxs)(n.li,{children:["\n",(0,s.jsxs)(n.p,{children:[(0,s.jsx)(n.strong,{children:"repr_args"}),"(self) -> 'ReprArgs'"]}),"\n",(0,s.jsxs)(n.ul,{children:["\n",(0,s.jsxs)(n.li,{children:["Returns the attributes to show in ",(0,s.jsx)(n.strong,{children:"str"}),", ",(0,s.jsx)(n.strong,{children:"repr"}),", and ",(0,s.jsx)(n.strong,{children:"pretty"})," this is generally overridden."]}),"\n"]}),"\n"]}),"\n"]}),"\n",(0,s.jsx)(n.p,{children:"Can either return:"}),"\n",(0,s.jsxs)(n.ul,{children:["\n",(0,s.jsxs)(n.li,{children:["\n",(0,s.jsxs)(n.p,{children:["name - value pairs, e.g.: ",(0,s.jsx)(n.code,{children:"[('foo_name', 'foo'), ('bar_name', ['b', 'a', 'r'])]"})]}),"\n"]}),"\n",(0,s.jsxs)(n.li,{children:["\n",(0,s.jsxs)(n.p,{children:["or, just values, e.g.: ",(0,s.jsx)(n.code,{children:"[(None, 'foo'), (None, ['b', 'a', 'r'])]"})]}),"\n"]}),"\n",(0,s.jsxs)(n.li,{children:["\n",(0,s.jsxs)(n.p,{children:[(0,s.jsx)(n.strong,{children:"repr_name"}),"(self) -> str"]}),"\n",(0,s.jsxs)(n.ul,{children:["\n",(0,s.jsxs)(n.li,{children:["Name of the instance's class, used in ",(0,s.jsx)(n.strong,{children:"repr"}),"."]}),"\n"]}),"\n"]}),"\n",(0,s.jsxs)(n.li,{children:["\n",(0,s.jsxs)(n.p,{children:[(0,s.jsx)(n.strong,{children:"repr_str"}),"(self, join_str: str) -> str"]}),"\n",(0,s.jsxs)(n.ul,{children:["\n",(0,s.jsx)(n.li,{children:"No docstring available."}),"\n"]}),"\n"]}),"\n",(0,s.jsxs)(n.li,{children:["\n",(0,s.jsxs)(n.p,{children:[(0,s.jsx)(n.strong,{children:"rich_repr"}),"(self) -> 'RichReprResult'"]}),"\n",(0,s.jsxs)(n.ul,{children:["\n",(0,s.jsx)(n.li,{children:"Get fields for Rich library"}),"\n"]}),"\n"]}),"\n",(0,s.jsxs)(n.li,{children:["\n",(0,s.jsxs)(n.p,{children:[(0,s.jsx)(n.strong,{children:"setattr"}),"(self, name, value)"]}),"\n",(0,s.jsxs)(n.ul,{children:["\n",(0,s.jsx)(n.li,{children:"Implement setattr(self, name, value)."}),"\n"]}),"\n"]}),"\n",(0,s.jsxs)(n.li,{children:["\n",(0,s.jsxs)(n.p,{children:[(0,s.jsx)(n.strong,{children:"setstate"}),"(self, state: 'DictAny') -> None"]}),"\n",(0,s.jsxs)(n.ul,{children:["\n",(0,s.jsx)(n.li,{children:"No docstring available."}),"\n"]}),"\n"]}),"\n",(0,s.jsxs)(n.li,{children:["\n",(0,s.jsxs)(n.p,{children:[(0,s.jsx)(n.strong,{children:"str"}),"(self) -> str"]}),"\n",(0,s.jsxs)(n.ul,{children:["\n",(0,s.jsx)(n.li,{children:"Return str(self)."}),"\n"]}),"\n"]}),"\n",(0,s.jsxs)(n.li,{children:["\n",(0,s.jsx)(n.p,{children:"_calculate_keys(self, include: Optional[ForwardRef('MappingIntStrAny')], exclude: Optional[ForwardRef('MappingIntStrAny')], exclude_unset: bool, update: Optional[ForwardRef('DictStrAny')] = None) -> Optional[AbstractSet[str]]"}),"\n",(0,s.jsxs)(n.ul,{children:["\n",(0,s.jsx)(n.li,{children:"No docstring available."}),"\n"]}),"\n"]}),"\n",(0,s.jsxs)(n.li,{children:["\n",(0,s.jsx)(n.p,{children:"_copy_and_set_values(self: 'Model', values: 'DictStrAny', fields_set: 'SetStr', *, deep: bool) -> 'Model'"}),"\n",(0,s.jsxs)(n.ul,{children:["\n",(0,s.jsx)(n.li,{children:"No docstring available."}),"\n"]}),"\n"]}),"\n",(0,s.jsxs)(n.li,{children:["\n",(0,s.jsx)(n.p,{children:"_extract_id(self, url)"}),"\n",(0,s.jsxs)(n.ul,{children:["\n",(0,s.jsx)(n.li,{children:"No docstring available."}),"\n"]}),"\n"]}),"\n",(0,s.jsxs)(n.li,{children:["\n",(0,s.jsx)(n.p,{children:"_fetch_files_recursive(self, service: Any, folder_id: str) -> List[Dict[str, Union[str, List[str]]]]"}),"\n",(0,s.jsxs)(n.ul,{children:["\n",(0,s.jsx)(n.li,{children:"Fetch all files and subfolders recursively."}),"\n"]}),"\n"]}),"\n",(0,s.jsxs)(n.li,{children:["\n",(0,s.jsx)(n.p,{children:"_init_private_attributes(self) -> None"}),"\n",(0,s.jsxs)(n.ul,{children:["\n",(0,s.jsx)(n.li,{children:"No docstring available."}),"\n"]}),"\n"]}),"\n",(0,s.jsxs)(n.li,{children:["\n",(0,s.jsx)(n.p,{children:"_iter(self, to_dict: bool = False, by_alias: bool = False, include: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny'), NoneType] = None, exclude: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny'), NoneType] = None, exclude_unset: bool = False, exclude_defaults: bool = False, exclude_none: bool = False) -> 'TupleGenerator'"}),"\n",(0,s.jsxs)(n.ul,{children:["\n",(0,s.jsx)(n.li,{children:"No docstring available."}),"\n"]}),"\n"]}),"\n",(0,s.jsxs)(n.li,{children:["\n",(0,s.jsx)(n.p,{children:"_load_credentials(self) -> Any"}),"\n",(0,s.jsxs)(n.ul,{children:["\n",(0,s.jsx)(n.li,{children:"Load credentials.\nThe order of loading credentials:"}),"\n"]}),"\n"]}),"\n"]}),"\n",(0,s.jsxs)(n.ol,{children:["\n",(0,s.jsx)(n.li,{children:"Service account key if file exists"}),"\n",(0,s.jsx)(n.li,{children:"Token path (for OAuth Client) if file exists"}),"\n",(0,s.jsx)(n.li,{children:"Credentials path (for OAuth Client) if file exists"}),"\n",(0,s.jsx)(n.li,{children:"Default credentials. if no credentials found, raise DefaultCredentialsError"}),"\n"]}),"\n",(0,s.jsxs)(n.ul,{children:["\n",(0,s.jsxs)(n.li,{children:["\n",(0,s.jsx)(n.p,{children:"_load_document_from_id(self, id: str) -> langchain_core.documents.base.Document"}),"\n",(0,s.jsxs)(n.ul,{children:["\n",(0,s.jsx)(n.li,{children:"Load a document from an ID."}),"\n"]}),"\n"]}),"\n",(0,s.jsxs)(n.li,{children:["\n",(0,s.jsx)(n.p,{children:"_load_documents_from_folder(self, folder_id: str, *, file_types: Optional[Sequence[str]] = None) -> List[langchain_core.documents.base.Document]"}),"\n",(0,s.jsxs)(n.ul,{children:["\n",(0,s.jsx)(n.li,{children:"Load documents from a folder."}),"\n"]}),"\n"]}),"\n",(0,s.jsxs)(n.li,{children:["\n",(0,s.jsx)(n.p,{children:"_load_documents_from_ids(self) -> List[langchain_core.documents.base.Document]"}),"\n",(0,s.jsxs)(n.ul,{children:["\n",(0,s.jsx)(n.li,{children:"Load documents from a list of IDs."}),"\n"]}),"\n"]}),"\n",(0,s.jsxs)(n.li,{children:["\n",(0,s.jsx)(n.p,{children:"_load_file_from_id(self, id: str) -> List[langchain_core.documents.base.Document]"}),"\n",(0,s.jsxs)(n.ul,{children:["\n",(0,s.jsx)(n.li,{children:"Load a file from an ID."}),"\n"]}),"\n"]}),"\n",(0,s.jsxs)(n.li,{children:["\n",(0,s.jsx)(n.p,{children:"_load_file_from_ids(self) -> List[langchain_core.documents.base.Document]"}),"\n",(0,s.jsxs)(n.ul,{children:["\n",(0,s.jsx)(n.li,{children:"Load files from a list of IDs."}),"\n"]}),"\n"]}),"\n",(0,s.jsxs)(n.li,{children:["\n",(0,s.jsx)(n.p,{children:"_load_sheet_from_id(self, id: str) -> List[langchain_core.documents.base.Document]"}),"\n",(0,s.jsxs)(n.ul,{children:["\n",(0,s.jsx)(n.li,{children:"Load a sheet and all tabs from an ID."}),"\n"]}),"\n"]}),"\n",(0,s.jsxs)(n.li,{children:["\n",(0,s.jsx)(n.p,{children:"alazy_load(self) -> 'AsyncIterator[Document]'"}),"\n",(0,s.jsxs)(n.ul,{children:["\n",(0,s.jsx)(n.li,{children:"A lazy loader for Documents."}),"\n"]}),"\n"]}),"\n",(0,s.jsxs)(n.li,{children:["\n",(0,s.jsx)(n.p,{children:"aload(self) -> 'List[Document]'"}),"\n",(0,s.jsxs)(n.ul,{children:["\n",(0,s.jsx)(n.li,{children:"Load data into Document objects."}),"\n"]}),"\n"]}),"\n",(0,s.jsxs)(n.li,{children:["\n",(0,s.jsx)(n.p,{children:"copy(self: 'Model', *, include: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny'), NoneType] = None, exclude: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny'), NoneType] = None, update: Optional[ForwardRef('DictStrAny')] = None, deep: bool = False) -> 'Model'"}),"\n",(0,s.jsxs)(n.ul,{children:["\n",(0,s.jsx)(n.li,{children:"Duplicate a model, optionally choose which fields to include, exclude and change."}),"\n"]}),"\n"]}),"\n"]}),"\n",(0,s.jsxs)(n.p,{children:[":param"," include: fields to include in new model\n",":param"," exclude: fields to exclude from new model, as with values this takes precedence over include\n",":param"," update: values to change/add in the new model. Note: the data is not validated before creating\nthe new model: you should trust this data\n",":param"," deep: set to ",(0,s.jsx)(n.code,{children:"True"})," to make a deep copy of the model\n:return: new model instance"]}),"\n",(0,s.jsxs)(n.ul,{children:["\n",(0,s.jsxs)(n.li,{children:["\n",(0,s.jsx)(n.p,{children:"dict(self, *, include: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny'), NoneType] = None, exclude: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny'), NoneType] = None, by_alias: bool = False, skip_defaults: Optional[bool] = None, exclude_unset: bool = False, exclude_defaults: bool = False, exclude_none: bool = False) -> 'DictStrAny'"}),"\n",(0,s.jsxs)(n.ul,{children:["\n",(0,s.jsx)(n.li,{children:"Generate a dictionary representation of the model, optionally specifying which fields to include or exclude."}),"\n"]}),"\n"]}),"\n",(0,s.jsxs)(n.li,{children:["\n",(0,s.jsx)(n.p,{children:"json(self, *, include: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny'), NoneType] = None, exclude: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny'), NoneType] = None, by_alias: bool = False, skip_defaults: Optional[bool] = None, exclude_unset: bool = False, exclude_defaults: bool = False, exclude_none: bool = False, encoder: Optional[Callable[[Any], Any]] = None, models_as_dict: bool = True, **dumps_kwargs: Any) -> str"}),"\n",(0,s.jsxs)(n.ul,{children:["\n",(0,s.jsxs)(n.li,{children:["Generate a JSON representation of the model, ",(0,s.jsx)(n.code,{children:"include"})," and ",(0,s.jsx)(n.code,{children:"exclude"})," arguments as per ",(0,s.jsx)(n.code,{children:"dict()"}),"."]}),"\n"]}),"\n"]}),"\n"]}),"\n",(0,s.jsxs)(n.p,{children:[(0,s.jsx)(n.code,{children:"encoder"})," is an optional function to supply as ",(0,s.jsx)(n.code,{children:"default"})," to json.dumps(), other arguments as per ",(0,s.jsx)(n.code,{children:"json.dumps()"}),"."]}),"\n",(0,s.jsxs)(n.ul,{children:["\n",(0,s.jsxs)(n.li,{children:["\n",(0,s.jsx)(n.p,{children:"lazy_load(self) -> 'Iterator[Document]'"}),"\n",(0,s.jsxs)(n.ul,{children:["\n",(0,s.jsx)(n.li,{children:"A lazy loader for Documents."}),"\n"]}),"\n"]}),"\n",(0,s.jsxs)(n.li,{children:["\n",(0,s.jsx)(n.p,{children:"load(self) -> List[langchain_core.documents.base.Document]"}),"\n",(0,s.jsxs)(n.ul,{children:["\n",(0,s.jsx)(n.li,{children:"Load documents."}),"\n"]}),"\n"]}),"\n",(0,s.jsxs)(n.li,{children:["\n",(0,s.jsx)(n.p,{children:"load_and_split(self, text_splitter: 'Optional[TextSplitter]' = None) -> 'List[Document]'"}),"\n",(0,s.jsxs)(n.ul,{children:["\n",(0,s.jsx)(n.li,{children:"Load Documents and split into chunks. Chunks are returned as Documents."}),"\n"]}),"\n"]}),"\n"]}),"\n",(0,s.jsx)(n.p,{children:"Do not override this method. It should be considered to be deprecated!"}),"\n",(0,s.jsx)(n.p,{children:"Args:\ntext_splitter: TextSplitter instance to use for splitting documents.\nDefaults to RecursiveCharacterTextSplitter."}),"\n",(0,s.jsx)(n.p,{children:"Returns:\nList of Documents."}),"\n",(0,s.jsxs)(n.ul,{children:["\n",(0,s.jsxs)(n.li,{children:["load_from_url(self, url: str)","\n",(0,s.jsxs)(n.ul,{children:["\n",(0,s.jsx)(n.li,{children:"No docstring available."}),"\n"]}),"\n"]}),"\n"]})]})}function h(e={}){const{wrapper:n}={...(0,r.R)(),...e.components};return n?(0,s.jsx)(n,{...e,children:(0,s.jsx)(c,{...e})}):c(e)}},8453:(e,n,l)=>{l.d(n,{R:()=>t,x:()=>d});var s=l(6540);const r={},i=s.createContext(r);function t(e){const n=s.useContext(i);return s.useMemo((function(){return"function"==typeof e?e(n):{...n,...e}}),[n,e])}function d(e){let n;return n=e.disableParentContext?"function"==typeof e.components?e.components(r):e.components||r:t(e.components),s.createElement(i.Provider,{value:n},e.children)}}}]);