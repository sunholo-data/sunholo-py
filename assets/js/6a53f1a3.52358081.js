"use strict";(self.webpackChunkdocs=self.webpackChunkdocs||[]).push([[1791],{8032:(e,n,t)=>{t.r(n),t.d(n,{Highlight:()=>h,assets:()=>c,contentTitle:()=>l,default:()=>p,frontMatter:()=>r,metadata:()=>d,toc:()=>u});var s=t(4848),o=t(8453),a=t(2800),i=t(5208);const r={title:"Dynamic UIs in Markdown using GenAI, React Components and MDX",authors:"me",tags:["agents","ux"],image:"https://dev.sunholo.com/assets/images/cognitive-design-ec3719c6b00a22113dd45194210067fa.webp",slug:"/dynamic-output-mdx"},l=void 0,d={permalink:"/blog/dynamic-output-mdx",source:"@site/blog/2024-10-15-dynamic-output-with-mdx.mdx",title:"Dynamic UIs in Markdown using GenAI, React Components and MDX",description:"Every few years I feel the need to change my blogging platform, and each time I am compelled to write a blog post about the exciting new blog tech.  I've moved through Blogpost, Wordpress, Posterous, Jenkins, Hugo and today I'd like to introduce Docusaurus.",date:"2024-10-15T00:00:00.000Z",tags:[{inline:!0,label:"agents",permalink:"/blog/tags/agents"},{inline:!0,label:"ux",permalink:"/blog/tags/ux"}],readingTime:10.81,hasTruncateMarker:!0,authors:[{name:"Mark Edmondson",title:"Founder",url:"https://sunholo.com/",imageURL:"https://code.markedmondson.me/images/gde_avatar.jpg",socials:{github:"https://github.com/MarkEdmondson1234",linkedin:"https://www.linkedin.com/in/markpeteredmondson/"},key:"me",page:null}],frontMatter:{title:"Dynamic UIs in Markdown using GenAI, React Components and MDX",authors:"me",tags:["agents","ux"],image:"https://dev.sunholo.com/assets/images/cognitive-design-ec3719c6b00a22113dd45194210067fa.webp",slug:"/dynamic-output-mdx"},unlisted:!1,nextItem:{title:"Using Cognitive Design to create a BigQuery Agent",permalink:"/blog/cognitive-design"}},c={authorsImageUrls:[void 0]},h=({children:e,color:n})=>{const t={span:"span",...(0,o.R)()};return(0,s.jsx)(t.span,{style:{backgroundColor:n,borderRadius:"2px",color:"#fff",padding:"0.2rem"},children:e})},u=[{value:"Introduction to MDX",id:"introduction-to-mdx",level:2},{value:"Dynamic UI Plots",id:"dynamic-ui-plots",level:3},{value:"MDX + GenAI = Dynamic UI",id:"mdx--genai--dynamic-ui",level:2},{value:"Creating Dynamic UIs in Markdown",id:"creating-dynamic-uis-in-markdown",level:2},{value:"Build vs render",id:"build-vs-render",level:3},{value:"Plan for failure",id:"plan-for-failure",level:3},{value:"Dummy data example",id:"dummy-data-example",level:2},{value:"API data calls",id:"api-data-calls",level:2},{value:"Calling a GenAI API to make a Dynamic UI",id:"calling-a-genai-api-to-make-a-dynamic-ui",level:3},{value:"Bat pie",id:"bat-pie",level:4},{value:"Reactive UI prompts",id:"reactive-ui-prompts",level:3},{value:"Summary",id:"summary",level:2}];function m(e){const n={a:"a",admonition:"admonition",blockquote:"blockquote",br:"br",code:"code",h2:"h2",h3:"h3",h4:"h4",img:"img",li:"li",p:"p",pre:"pre",strong:"strong",ul:"ul",...(0,o.R)(),...e.components};return(0,s.jsxs)(s.Fragment,{children:[(0,s.jsx)(n.p,{children:(0,s.jsx)(n.img,{src:t(1518).A+"",width:"1698",height:"624"})}),"\n",(0,s.jsxs)(n.p,{children:["Every few years I feel the need to change my blogging platform, and each time I am compelled to write a blog post about the exciting new blog tech.  I've moved through Blogpost, Wordpress, Posterous, Jenkins, Hugo and today I'd like to introduce ",(0,s.jsx)(n.a,{href:"https://docusaurus.io/",children:"Docusaurus"}),"."]}),"\n",(0,s.jsx)(n.p,{children:"And since this is a GenAI blog, it makes sense I selected a new blogging platform I feel will support GenAI.  Its a little thought provoking that the current GenAI models work best when working with the most popular languages, frameworks or opinions. They are after all approximating the average of all of human expression.  This means they will do better at English, Python and React than more niche areas such as Danish, R or Vue.  I hope this does not destroy diversity."}),"\n",(0,s.jsx)(n.p,{children:"But it also means that since it seems React is the most popular web frontend framework at the moment, it makes sense to investigate using React within GenAI applications."}),"\n",(0,s.jsx)(n.p,{children:"This Docusaurus blog is written in a flavour of Markdown that supports React Components which made me think: is this a good vessel for creating GenAI output that can dynamically adjust its output format?  Can we go beyond text to dynamic user experiences depending on what they need?  Lets find out."}),"\n","\n",(0,s.jsx)(n.h2,{id:"introduction-to-mdx",children:"Introduction to MDX"}),"\n",(0,s.jsxs)(n.p,{children:[(0,s.jsx)(n.a,{href:"https://mdxjs.com/",children:"MDX"})," allows you to write markdown and React javascript in the same file.",(0,s.jsx)(n.br,{}),"\n","For example, I can write this to create some unique highlights, dynamically within this post:"]}),"\n",(0,s.jsx)(n.pre,{children:(0,s.jsx)(n.code,{className:"language-js",children:"export const Highlight = ({children, color}) => (\n  <span\n    style={{\n      backgroundColor: color,\n      borderRadius: '2px',\n      color: '#fff',\n      padding: '0.2rem',\n    }}>\n    {children}\n  </span>\n);\n\nThis is quoted using normal Markdown syntax but then modified with a React addition via .mdx:\n\n:::info\n<Highlight color=\"#c94435\">Sunholo Shades</Highlight> are <Highlight color=\"#d47758\">the best solar shades</Highlight>\n:::\n"})}),"\n","\n",(0,s.jsx)(n.p,{children:"This is quoted using normal Markdown syntax but then modified with a React addition via .mdx:"}),"\n",(0,s.jsx)(n.admonition,{type:"info",children:(0,s.jsxs)(n.p,{children:[(0,s.jsx)(h,{color:"#c94435",children:"Sunholo Shades"})," are ",(0,s.jsx)(h,{color:"#d47758",children:"the best solar shades"}),"."]})}),"\n",(0,s.jsx)(n.h3,{id:"dynamic-ui-plots",children:"Dynamic UI Plots"}),"\n",(0,s.jsxs)(n.p,{children:["And since any(?) React component is usable, then importing libraries such as ",(0,s.jsx)(n.a,{href:"https://plotly.com/javascript/react/",children:"Plot.ly"})," allows you to embed capabilities beyond text, to produce interactive graphics and data analysis."]}),"\n",(0,s.jsx)(n.p,{children:"In this example I first installed plot.ly:"}),"\n",(0,s.jsx)(n.pre,{children:(0,s.jsx)(n.code,{className:"language-sh",children:"yarn add react-plotly.js plotly.js\n"})}),"\n",(0,s.jsx)(n.p,{children:"Naively, I then added this to the top of the blog markdown:"}),"\n",(0,s.jsx)(n.pre,{children:(0,s.jsx)(n.code,{className:"language-sh",children:"import Plot from 'react-plotly.js';\n"})}),"\n",(0,s.jsx)(n.p,{children:"...and could then display plots:"}),"\n",(0,s.jsx)(n.pre,{children:(0,s.jsx)(n.code,{className:"language-js",children:"<Plot\n  data={[\n    {\n      x: [1, 2, 3, 4],\n      y: [10, 15, 13, 17],\n      type: 'scatter',\n      mode: 'lines+markers',\n      marker: { color: '#c94435' },\n    },\n  ]}\n  layout={{\n    title: 'Simple Plot',\n    autosize: true,\n    margin: { t: 30, l: 30, r: 30, b: 30 },\n  }}\n  useResizeHandler\n  style={{ width: '100%', height: '300px' }}\n/>\n"})}),"\n",(0,s.jsx)(n.p,{children:"That worked for runtime, but broke in build time with:"}),"\n",(0,s.jsxs)(n.admonition,{type:"danger",children:[(0,s.jsx)(n.p,{children:"It looks like you are using code that should run on the client-side only.\nTo get around it, try using one of:"}),(0,s.jsxs)(n.ul,{children:["\n",(0,s.jsxs)(n.li,{children:[(0,s.jsx)(n.code,{children:"<BrowserOnly>"})," (",(0,s.jsx)(n.a,{href:"https://docusaurus.io/docs/docusaurus-core/#browseronly",children:"https://docusaurus.io/docs/docusaurus-core/#browseronly"}),")"]}),"\n",(0,s.jsxs)(n.li,{children:[(0,s.jsx)(n.code,{children:"ExecutionEnvironment"})," (",(0,s.jsx)(n.a,{href:"https://docusaurus.io/docs/docusaurus-core/#executionenvironment",children:"https://docusaurus.io/docs/docusaurus-core/#executionenvironment"}),")."]}),"\n"]})]}),"\n",(0,s.jsx)(n.p,{children:"Plot.ly depends on runtime attributes such as the browser window that breaks on build, so a custom wrapper is needed to handle loading in the plot.ly library."}),"\n",(0,s.jsx)(n.pre,{children:(0,s.jsx)(n.code,{className:"language-js",children:"\nconst CustomPlot = ({ data, layout }) => {\n  const [Plot, setPlot] = useState(null);\n\n  // Dynamically import `react-plotly.js` on the client side\n  useEffect(() => {\n    let isMounted = true;\n    import('react-plotly.js').then((module) => {\n      if (isMounted) {\n        setPlot(() => module.default);\n      }\n    });\n\n    return () => {\n      isMounted = false; // Cleanup to prevent memory leaks\n    };\n  }, []);\n\n  if (!Plot) {\n    return <div>Loading Plot...</div>; // Show a loading state while Plotly is being imported\n  }\n\n  return (\n    <Plot\n      data={data}\n      layout={layout || {\n        title: 'Default Plot',\n        autosize: true,\n        margin: { t: 30, l: 30, r: 30, b: 30 },\n      }}\n      useResizeHandler\n      style={{ width: '100%', height: '300px' }}\n    />\n  );\n};\n\nexport default CustomPlot;\n"})}),"\n",(0,s.jsx)(n.p,{children:"This then renders correctly at run and build time:"}),"\n",(0,s.jsx)(n.p,{children:(0,s.jsx)(n.code,{children:"<CustomPlot />"})}),"\n",(0,s.jsx)(a.A,{}),"\n",(0,s.jsx)(n.p,{children:"This shows potential.  What other elements could be rendered, and how can GenAI render them on the fly?"}),"\n",(0,s.jsx)(n.h2,{id:"mdx--genai--dynamic-ui",children:"MDX + GenAI = Dynamic UI"}),"\n",(0,s.jsx)(n.p,{children:"If you hadn't guessed already, the above code was already created by a GenAI model.  I am a data engineer, not a front-end software engineer (and from what I see, frontend UI is why more complex than data science!).  It does seems viable to request a model to output React components, and if that text is within an environment that supports its display, we will instead render the component instead of the text.\nI would also like to control what is rendered, by specifying the components at runtime, so we can configure those components to not need many arguments and make it as easy as possible for the model to render. We should only need to ask nicely."}),"\n",(0,s.jsxs)(n.p,{children:["We know via ",(0,s.jsx)(n.a,{href:"https://www.anthropic.com/news/artifacts",children:"Anthropic's Artifacts"})," or ",(0,s.jsx)(n.a,{href:"https://v0.dev/",children:"v0 Chat"}),", dynamic rendering is very much possible.  We are looking to create a subset of that functionality: not looking for the ability to render ",(0,s.jsx)(n.strong,{children:"any"})," React, just the controlled Components we prompt the model to return."]}),"\n",(0,s.jsx)(n.p,{children:'Another more "standard" solution is to have the chat bot use function calling, that return components.  Maybe that\'s better, who knows.'}),"\n",(0,s.jsx)(n.p,{children:"For example, a GenAI prompt could include:"}),"\n",(0,s.jsxs)(n.blockquote,{children:["\n",(0,s.jsxs)(n.p,{children:["...every time you output a colour, make sure to quote it in ",(0,s.jsx)(n.code,{children:"<Highlight>"})," tags with the colour e.g. ",(0,s.jsx)(n.code,{children:'<Highlight color="#c94435">Sunholo Shades</Highlight>'}),"..."]}),"\n"]}),"\n",(0,s.jsx)(n.p,{children:"A more exciting prompt could be:"}),"\n",(0,s.jsxs)(n.blockquote,{children:["\n",(0,s.jsxs)(n.p,{children:["...every time you get data that can be displayed as a line chart (e.g. x and y values) then render those values using ",(0,s.jsx)(n.code,{children:"<CustomPlot />"})," e.g. ",(0,s.jsx)(n.code,{children:"<CustomPlot data={[{x: [1, 2, 3, 4],y: [10, 15, 13, 17]}]}/>"}),"..."]}),"\n"]}),"\n",(0,s.jsxs)(n.p,{children:["...assuming we have created ",(0,s.jsx)(n.code,{children:"<CustomPlot />"})," with some sensible defaults."]}),"\n",(0,s.jsx)(n.h2,{id:"creating-dynamic-uis-in-markdown",children:"Creating Dynamic UIs in Markdown"}),"\n",(0,s.jsxs)(n.p,{children:["It just so happens, that I had a prototype Chat React Component lying around as one of ",(0,s.jsx)(n.a,{href:"/docs/multivac/#user-interfaces",children:"Multivac's UI options"}),", and I can use it to stream custom GenAI APIs, so I'll attempt to host that Chat UI within this blog post, ask it to output MDX format, and then render them within the blog using MDX."]}),"\n",(0,s.jsx)(n.h3,{id:"build-vs-render",children:"Build vs render"}),"\n",(0,s.jsx)(n.p,{children:"Lessons learnt whilst attempting this were:"}),"\n",(0,s.jsxs)(n.ul,{children:["\n",(0,s.jsx)(n.li,{children:"Components will only respect the rules within that component, not outside."}),"\n",(0,s.jsxs)(n.li,{children:["The MDX examples above are created during ",(0,s.jsx)(n.code,{children:"yarn build"}),", not upon render.  Another approach is needed to render in real-time as the chat returns results e.g. the JSX Parser below."]}),"\n",(0,s.jsxs)(n.li,{children:["But it works the other way around too - not all Components that work at render time will work at build time, as they depend on website elements (e.g. Plot.ly).  You may need ",(0,s.jsx)(n.code,{children:"<BrowserOnly>"})," to help here to avoid build time errors."]}),"\n"]}),"\n",(0,s.jsxs)(n.p,{children:["For now, to render React dynamically we're going to need at least the package ",(0,s.jsx)(n.a,{href:"https://github.com/TroyAlford/react-jsx-parser",children:(0,s.jsx)(n.code,{children:"react-jsx-parser"})}),", installed via:"]}),"\n",(0,s.jsx)(n.pre,{children:(0,s.jsx)(n.code,{className:"language-sh",children:"yarn add react-jsx-parser\n"})}),"\n",(0,s.jsxs)(n.p,{children:["I can then use its ",(0,s.jsx)(n.code,{children:"JXParser()"})," and send in the components from the .mdx file on which it will allow:"]}),"\n",(0,s.jsx)(n.pre,{children:(0,s.jsx)(n.code,{className:"language-js",children:"<JSXParser\n    jsx={message}\n    components={components} // Pass components dynamically\n    renderInWrapper={false}\n    allowUnknownElements={false}\n    blacklistedTags={['script', 'style', 'iframe', 'link', 'meta']}\n/>\n"})}),"\n",(0,s.jsxs)(n.p,{children:["You can see all the code for the ",(0,s.jsx)(n.a,{href:"https://github.com/sunholo-data/sunholo-py/blob/main/docs/src/components/multivacChat.js",children:"MultivacChatMessage here"}),", and the ",(0,s.jsx)(n.a,{href:"https://github.com/sunholo-data/sunholo-py/blob/main/docs/src/components/mdxComponents.js",children:"CustomPlot here"}),"."]}),"\n",(0,s.jsx)(n.h3,{id:"plan-for-failure",children:"Plan for failure"}),"\n",(0,s.jsxs)(n.p,{children:["Another situation we need to deal with non-deterministic GenAI output is that it will likely fail at some point, and we need to make sure that if it outputs invalid Components it doesn't bork the entire text.  After a few iterations, turning on many of the ",(0,s.jsx)(n.a,{href:"https://www.npmjs.com/package/react-jsx-parser?activeTab=readme",children:"JSX flags as documented here"})," helped make the output more reliable."]}),"\n",(0,s.jsx)(n.pre,{children:(0,s.jsx)(n.code,{className:"language-js",children:"<JSXParser\n    jsx={message}\n    components={components}\n    renderInWrapper={false}\n    allowUnknownElements={false}\n    autoCloseVoidElements\n    showWarnings\n    componentsOnly\n    blacklistedTags={['script', 'style', 'iframe', 'link', 'meta']}\n    onError={(error) => {\n        console.error('onError parsing JSX:', error);\n        }\n    } \n/>\n"})}),"\n",(0,s.jsx)(n.h2,{id:"dummy-data-example",children:"Dummy data example"}),"\n",(0,s.jsxs)(n.p,{children:["I now add the component to the .mdx file below, passing in either imported components (",(0,s.jsx)(n.code,{children:"CustomPlot"}),") or components defined within the .mdx file itself (",(0,s.jsx)(n.code,{children:"Highlight"}),"):"]}),"\n",(0,s.jsx)(n.pre,{children:(0,s.jsx)(n.code,{className:"language-html",children:"<MultivacChatMessage components={{ Highlight, CustomPlot }} />\n"})}),"\n",(0,s.jsx)(n.p,{children:"Go ahead, give it a try below by typing something into the chat box."}),"\n",(0,s.jsx)(n.p,{children:"This one has a dummy API call that will always return the same mix of markdown, but importantly its not rendering itself, just pulling in text which we are controlling from the .mdx file:"}),"\n",(0,s.jsx)(n.pre,{children:(0,s.jsx)(n.code,{className:"language-js",children:"const dummyResponse = `This is normal markdown. <Highlight color=\"#c94435\">This is a highlighted response</Highlight>. This is a CustomPlot component:\n<CustomPlot data={[\n    { x: [1, 2, 3, 4], y: [10, 15, 13, 17], type: 'scatter', mode: 'lines+markers' }\n]} />\n`;\n"})}),"\n",(0,s.jsx)(n.p,{children:"The model only returns text, no functions, but we still see pretty rendering as MDX operates on that text."}),"\n",(0,s.jsx)(i.A,{components:{Highlight:h,CustomPlot:a.A},debug:!0}),"\n",(0,s.jsx)(n.h2,{id:"api-data-calls",children:"API data calls"}),"\n",(0,s.jsxs)(n.p,{children:["Now lets do it with a real API call, as documented in the ",(0,s.jsx)(n.a,{href:"https://github.com/sunholo-data/sunholo-py/blob/6ad6287f7eb8a7c4762a087db4fae55059051c26/docs/src/components/multivacChat.js#L51",children:"multivacChat.js script"}),"."]}),"\n",(0,s.jsx)(n.pre,{children:(0,s.jsx)(n.code,{className:"language-js",children:"const fetchRealData = async () => {\n    setLoading(true);\n    setError(null);\n    setMessage('');\n\n    if (!apiKey) {\n      setError(\"Missing API key.\");\n      setLoading(false);\n      return;\n    }\n\n    try {\n      const response = await fetch(`${API_BASE_URL}/vac/streaming/dynamic_blog_mdx`, {\n        method: 'POST',\n        headers: {\n          'Content-Type': 'application/json',\n          'x-api-key': apiKey,\n        },\n        body: JSON.stringify({ user_input: userInput, stream_only: true }),\n      });\n\n      if (!response.ok) {\n        throw new Error(`HTTP error! status: ${response.status}`);\n      }\n\n      const reader = response.body.getReader();\n      const decoder = new TextDecoder('utf-8');\n      let done = false;\n\n      while (!done) {\n        const { value, done: doneReading } = await reader.read();\n        done = doneReading;\n\n        if (value) {\n          const chunk = decoder.decode(value);\n          try {\n            const json = JSON.parse(chunk);\n            console.log(\"Ignoring JSON chunk:\", json);\n          } catch (e) {\n            setMessage((prev) => prev + chunk);\n          }\n        }\n      }\n    } catch (error) {\n      setError(`An error occurred while fetching data: ${error.message}`);\n    } finally {\n      setLoading(false);\n    }\n  };\n"})}),"\n",(0,s.jsxs)(n.p,{children:["I use a Vertex deployed API on ",(0,s.jsx)(n.a,{href:"/docs/multivac/",children:"Multivac"})," and make a new VAC called ",(0,s.jsx)(n.code,{children:"dynamic_blog_mdx"})," which has no tools, just a prompt that asks it to output the React components.  I call to my own Multivac cloud as this adds various features I want such as prompt management, analytics, configuration, user history etc. and runs custom code within a Cloud Run container."]}),"\n",(0,s.jsx)(n.admonition,{type:"tip",children:(0,s.jsx)(n.p,{children:"Multivac API requests are by no means required, you can modify the API call to be your own API or use a direct GenAI API call such as Gemini, Anthropic or OpenAI, or local hosted GenAI APIs via Ollama etc."})}),"\n",(0,s.jsxs)(n.p,{children:["I had to do some shenanigans for CORs within Docusaurus and proxy the API calls, you can see that code in the ",(0,s.jsx)(n.a,{href:"https://github.com/sunholo-data/sunholo-py/blob/main/docs/src/plugins/proxy.js",children:(0,s.jsx)(n.code,{children:"plugins/proxy.js"})})," but basically its just calling the streaming API and returning text chunks."]}),"\n",(0,s.jsx)(n.h3,{id:"calling-a-genai-api-to-make-a-dynamic-ui",children:"Calling a GenAI API to make a Dynamic UI"}),"\n",(0,s.jsxs)(n.p,{children:["This is using a Gemini's ",(0,s.jsx)(n.a,{href:"https://ai.google.dev/gemini-api/docs/models/gemini#gemini-1.5-flash-8b",children:"gemini-1.5-flash-8b"})," model which is super cheap but not the smartest model out there, but thats the point: the model doesn't have to think too much to render nicely, as we limit its choices to just those React components we send in."]}),"\n",(0,s.jsxs)(n.blockquote,{children:["\n",(0,s.jsx)(n.p,{children:"I'm scaling the Cloud Run to 0 for this example so if you try it be patient: on a cold start the first response will be a little slower than subsequent ones.  The model will also have no chat history."}),"\n"]}),"\n",(0,s.jsx)(i.A,{components:{Highlight:h,CustomPlot:a.A}}),"\n",(0,s.jsx)(n.h4,{id:"bat-pie",children:"Bat pie"}),"\n",(0,s.jsx)(n.p,{children:"You should see something like below, where I asked it to make a pie chart about bats:"}),"\n",(0,s.jsx)(n.p,{children:(0,s.jsx)(n.img,{src:t(4687).A+"",width:"1182",height:"1258"})}),"\n",(0,s.jsx)(n.h3,{id:"reactive-ui-prompts",children:"Reactive UI prompts"}),"\n",(0,s.jsxs)(n.p,{children:["One of the features of using Multivac is having a ",(0,s.jsx)(n.a,{href:"https://langfuse.com/docs/prompts/get-started",children:"prompt CMS via Langfuse"}),", so I can tweak the prompt as I tailor the responses:"]}),"\n",(0,s.jsx)(n.p,{children:(0,s.jsx)(n.img,{src:t(1073).A+"",width:"2160",height:"850"})}),"\n",(0,s.jsx)(n.p,{children:"The prompt for the above bot is similar to:"}),"\n",(0,s.jsx)(n.admonition,{type:"note",children:(0,s.jsxs)(n.p,{children:["You are demonstrating how to use React components in your generated text.",(0,s.jsx)(n.br,{}),"\n","The components have been already configured and you only need to use React Component tags for them to render to the user.\nThe ",(0,s.jsx)(n.code,{children:"<Highlight>"})," component lets you shade certain words: e.g. ",(0,s.jsx)(n.code,{children:'<Highlight color="#c94435">Sunholo Shades</Highlight>'}),"\nThe ",(0,s.jsx)(n.code,{children:"<CustomPlot />"})," component lets you display Plot.ly plots: e.g. ",(0,s.jsx)(n.code,{children:"<CustomPlot data={[{ x: [1, 2, 3, 4], y: [10, 15, 13, 17], type: 'scatter', mode: 'lines+markers' }]} />"}),"\nOveruse these components and try to squeeze both of them into every answer you give :)  Be funny about it.\nDon't worry about the context at all."]})}),"\n",(0,s.jsx)(n.h2,{id:"summary",children:"Summary"}),"\n",(0,s.jsx)(n.p,{children:"This was intended just to be a demo on what is possible with MDX to render dynamic React components in Markdown.  We've demonstrated a proof of concept which I will take further in my subsequent blog posts."}),"\n",(0,s.jsx)(n.p,{children:"Docusaurus is not the only platform that uses MDX, so this technique is applicable way beyond here."}),"\n",(0,s.jsxs)(n.p,{children:["I'm a complete n00b in React and front end in general so I hope more experienced folks may be able to chime in as describe how to do this better, but I think its a nice workflow for me, espeically for blog posts demonstrating GenAI ideas.  We have just used a simple chat box interface here, but I'd like to explore more professional component styling and how GenAI can turn unstructured data into structured data in more automated settings, leveraging cheap quick models such as Gemini Flash, sending in images, audio, video etc and getting back output.  I'm going to think about including dynamic UI output in all my ",(0,s.jsx)(n.a,{href:"/blog/cognitive-design",children:"cognitive designs"})," going forward, and having a way to do that in a user friendly markdown editor will help turn-around concepts quickly."]})]})}function p(e={}){const{wrapper:n}={...(0,o.R)(),...e.components};return n?(0,s.jsx)(n,{...e,children:(0,s.jsx)(m,{...e})}):m(e)}},2800:(e,n,t)=>{t.d(n,{A:()=>a});var s=t(6540),o=t(4848);const a=e=>{let{data:n,layout:a}=e;const[i,r]=(0,s.useState)(null);return(0,s.useEffect)((()=>{let e=!0;return t.e(1236).then(t.bind(t,1236)).then((n=>{e&&r((()=>n.default))})),()=>{e=!1}}),[]),i?(0,o.jsx)(i,{data:n,layout:a||{title:"Dynamic UI Plot",autosize:!0,margin:{t:30,l:30,r:30,b:30}},useResizeHandler:!0,style:{width:"100%",height:"300px"}}):(0,o.jsx)("div",{children:"Loading Plot..."})}},5208:(e,n,t)=>{t.d(n,{A:()=>d});var s=t(6540),o=t(3134),a=t(7639),i=t(9813),r=t(4848);const l=e=>e.replace(/<[^>]+>/g,"");const d=function(e){let{components:n,debug:t=!1}=e;const{siteConfig:d}=(0,a.A)(),[c,h]=(0,s.useState)(""),[u,m]=(0,s.useState)(""),[p,g]=(0,s.useState)(!1),[x,y]=(0,s.useState)(null),[j,f]=(0,s.useState)(""),w=d.customFields.multivacApiKey;(0,s.useEffect)((()=>()=>{m(""),y(null),g(!1),f("")}),[]);const b=e=>{e.preventDefault(),c.trim()?t?(async()=>{g(!0),y(null),m("");try{await new Promise((e=>setTimeout(e,2e3))),m("This is normal markdown. <Highlight color=\"#c94435\">This is a highlighted response</Highlight>. This is a CustomPlot component: <CustomPlot data={[{ x: [1, 2, 3, 4], y: [10, 15, 13, 17], type: 'scatter', mode: 'lines+markers' }]} />")}catch(x){y("An error occurred while fetching data.")}finally{g(!1)}})():(async()=>{if(g(!0),y(null),m(""),!w)return y("Missing API key."),void g(!1);try{const n=await fetch("https://vertex-genai-533923089340.europe-west1.run.app/vac/streaming/dynamic_blog_mdx",{method:"POST",headers:{"Content-Type":"application/json","x-api-key":w},body:JSON.stringify({user_input:c,stream_only:!0})});if(!n.ok)throw new Error(`HTTP error! status: ${n.status}`);const t=n.body.getReader(),s=new TextDecoder("utf-8");let o=!1;for(;!o;){const{value:n,done:a}=await t.read();if(o=a,n){const t=s.decode(n);try{const e=JSON.parse(t);console.log("Ignoring JSON chunk:",e)}catch(e){m((e=>e+t))}}}}catch(x){y(`An error occurred while fetching data: ${x.message}`)}finally{g(!1)}})():y("Input cannot be empty")},v=()=>{try{return(0,r.jsx)(o.A,{jsx:u,components:n,renderInWrapper:!1,allowUnknownElements:!1,autoCloseVoidElements:!0,showWarnings:!0,renderError:()=>(0,r.jsxs)("p",{children:["Failed to render: ",l(u)]}),componentsOnly:!0,blacklistedTags:["script","style","iframe","link","meta"],onError:e=>{console.error("onError parsing JSX:",e)}})}catch(e){return console.error("catch Error parsing JSX, attempting santize",l(u)),(0,r.jsx)("p",{children:l(u)})}};return(0,r.jsx)(i.A,{children:()=>(0,r.jsxs)("div",{className:"multivac-chat-container",children:[(0,r.jsxs)("form",{onSubmit:b,children:[(0,r.jsx)("input",{type:"text",placeholder:"Ask a question...",value:c,onChange:e=>h(e.target.value),className:"multivac-input"}),(0,r.jsx)("button",{type:"submit",disabled:p,className:"multivac-submit-btn",children:p?"Loading...":"Submit"})]}),p&&(0,r.jsx)("p",{children:"Fetching response..."}),x&&(0,r.jsx)("p",{className:"error-message",children:x}),(0,r.jsx)("div",{className:"multivac-message-output",children:u?v():null})]})})}},4687:(e,n,t)=>{t.d(n,{A:()=>s});const s=t.p+"assets/images/bat-pie-04b510eacf05b04a0dde1f64fc035d15.png"},1518:(e,n,t)=>{t.d(n,{A:()=>s});const s=t.p+"assets/images/dynamic-ui-banner-bef5ed4d0e16d5a3a781ae1928efab46.png"},1073:(e,n,t)=>{t.d(n,{A:()=>s});const s=t.p+"assets/images/mdx-prompt-langfuse-d9c7c8cb019b01bda9114e3f56e3e88b.png"}}]);