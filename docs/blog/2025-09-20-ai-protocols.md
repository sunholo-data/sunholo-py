---
title: "The AI Protocol Revolution: A Story of History Repeating Itself"
authors: me
tags: [mcp, a2a, agents]
slug: /ai-protocol-revolution
---

import AudioPlayer from '@site/src/components/audio';

Here at Sunholo, we've specialised deploying GenAI applications for the past few years. Recently, when talking to new propects we have noticed a trend: they show us their own internal chatbot, built at great expense just 18 months ago, and ask why it feels so outdated compared to ChatGPT or Gemini. Is there a better way to keep up to date but still keep your AI application bespoke? The answer takes us on a journey through web history, emerging protocols, and a future that's arriving faster than most realize.

<AudioPlayer src="https://storage.googleapis.com/sunholo-public-podcasts/The_Protocol_Wars__Why_Your_Custom_AI_Is_Failing_and_How_New_St.mp4" />

<!-- truncate -->



## AI Web = Web 1.0 / 2.0 ?

Remember Web 1.0? That nostalgic era of disparate hobby websites, the dot-com bubble, and the rise of search engines? In retrospect it could be said that during that era, companies offered read-only access to their databases in exchange for traffic and ad revenue.

Web 2.0 changed when companies started to let users WRITE as well as read to databases. Suddenly websites were updating in real-time with user generated content: blog comments, tweets, social interactions. Facebook and others then built walled gardens around their database monetised with personalized feeds, selling user behaviour to companies for highly targeted advertising. 

The AI evolution could be said to be following the same pattern, only accelerated. ChatGPT started with conversations with static models, enhanced only by chat history.  Then everyone got excited by vector embeddings and RAG for passing in more real-time data to the model. Now users and 3rd parties can bring their own data, as Agentic AI reaches out to other sources, and we're building toward something bigger. But there's a problem.

## The Integration Nightmare

MIT's recent study showing that 95% of generative AI pilots fail to achieve rapid revenue acceleration:

- [MIT report: 95% of generative AI pilots at companies are failing | Fortune](https://fortune.com/2025/08/18/mit-report-95-percent-generative-ai-pilots-at-companies-failing-cfo/) 

But that tells only part of the story. What they don't say is why.  One reason could be that to stay relevant, AI tool needed custom integration with every requested data source and AI systems, and that home-spun solutions to connect quickly become outdated as the rapid pace of improvements outpaces developer project time.

This is where our story takes an interesting turn.

## The Protocols Emerge (MCP & A2A)

In November 2024, Anthropic released the [Model Context Protocol (MCP)](https://www.anthropic.com/news/model-context-protocol), but this wasn't just another standard. It was an admission that the entire industry had been doing it wrong. MCP isn't particularly special in its properties—much like HTTP wasn't special. The magic comes when everyone adopts it.

Anthropic was the perfect source for this protocol. They're respected by developers for their coding capabilities but also neutral enough—deployed across Google Cloud, AWS, and Azure—to be trusted by everyone.

Then in April 2025, Google announced the Agent2Agent (A2A) protocol, backed by 50+ tech companies 

* [Announcing the Agent2Agent Protocol (A2A) - Google Developers Blog](https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/). 

While MCP connects AI to tools and data, A2A defines how AI agents collaborate. It's the difference between giving workers tools and teaching them to work as a team.

The protocol was deliberately kept vendor-neutral, transferred to an Apache project and endorsed by Microsoft and IBM. Like HTTP before it, A2A's value only emerges through universal adoption.

## The Commerce Layer Changes Everything

Google's recent Agent Payments Protocol (AP2), developed with 60+ organizations including Mastercard and PayPal 

- [Announcing Agent Payments Protocol (AP2) | Google Cloud Blog](https://cloud.google.com/blog/products/ai-machine-learning/announcing-agents-to-payments-ap2-protocol), 

AP2 adds what might be the most transformative element. This isn't just about AI agents buying things—it's about creating entirely new business models.

Imagine your analysis agent automatically hiring a specialist translation agent when it encounters foreign language documents, paying per use, no human involvement. The agent economy isn't coming; it's being built right now.

## The Living Laboratory

[Google Agentspace](https://cloud.google.com/products/agentspace), already deployed at companies like Wells Fargo, KPMG, and Nokia, shows what this infrastructure looks like in practice. It's one of Google Cloud's fastest-growing products ever, and watching it work is like seeing the future arrive early.

That dusty SharePoint archive from 2015? Suddenly searchable alongside this morning's Slack conversations. The rigid SAP system that took six months to integrate? Now accessible to AI agents without touching a line of code. Agentspace leverages A2A and has announced an A2A marketplace for seamless integration with its platform. The protocol works with all major AI frameworks such as Langchain and PydanticAI including Google's own ADK, demonstrating the power of unified AI access to enterprise data.

## The Second Wave Crisis

After two years in the AI trenches, we are seeing a pattern for those early adopters. A lot of companies that were cutting edge in 2023 — the ones who built chatbots plus RAG for internal document search — are now stuck. They can't keep up with the pace of model improvements by the hyperscalers. Every time Gemini, Claude or OpenAI releases an update such as artifacts, thinking tokens or code execution, they face months of integration work to match it.

This is the bitter lesson of AI: specialized solutions lose to general approaches that leverage computation. But we're learning a corollary: rigid infrastructure becomes tomorrow's technical debt, fast.

The solution isn't just technical—it's philosophical. Build for change, not features. Every AI component needs to be independently replaceable, like swapping batteries rather than rewiring your house. When OpenAI, Google or Claude releases a new model or feature next month (and they will), you should be able to swap it in within hours.  If you get it right, then your application automtically improves without you needing to change anything.  

Get it wrong however, and you are stuck with old features that your staff do not use in favour of "shadow AI" being used via personal phones or bypassing VPN controls.  Why that matters?  Those interactions are so valuable in assessing what your collegues are actually working on, what drives are important for your company.  Passing that to a 3rd party and not having those AI conversations available for your own review gives the keys to your busienss improvement to someone else, out of your control.

## The Non-Human Web Emerges

Humans are becoming less likely to be direct consumers of web data. We may have already reached peak human web traffic.

Google's AI Overviews now appear in over 35% of U.S. searches, with some sites reporting traffic drops of up to 70%. The Verge's publisher notes that when people see AI summaries, they visit sites less often .

* [AI Summaries causing devasting drop in online news audiences | Guardian](https://www.theguardian.com/technology/2025/jul/24/ai-summaries-causing-devastating-drop-in-online-news-audiences-study-finds). 

According to Pew Research, just 8% of users who encountered an AI summary clicked through to a traditional link—half the rate of those who didn't 

* [Pew Research Confirms Google AI Overviews Is Eroding Web Ecosystem | Search Engine Journal](https://www.searchenginejournal.com/pew-research-confirms-google-ai-overviews-is-eroding-web-ecosystem/551825/).

Think about your own behavior. How often do you ask ChatGPT or Google's AI for information instead of visiting websites yourself? Now multiply that by billions of users and add AI agents that never sleep, never get tired, and can visit thousands of sites per second.

Currently, there's a booming market for web scrapers—tools that help AI read websites designed for humans. But we propose that this is transitional, like mobile websites before responsive design. The same databases that generate HTML for humans will soon serve API responses via MCP and A2A directly to AI agents.

The rise of standards like [/llm.txt](https://llmstxt.org/) signals this shift—stripping away JavaScript complexity for plain text that AI can easily digest. We're building a parallel web for machines.

## The Business Model Breaking Point

The impact on media and content businesses is existential. Cloudflare data shows that for every visitor Anthropic refers back to a website, its crawlers have already visited tens of thousands of pages. OpenAI's crawler scraped websites 1,700 times for every referral, while Google's ratio was 14-to-1 

* [The crawl-to-click gap: Cloudflare data on AI bots, training, and referrals | Cloudflare](https://blog.cloudflare.com/crawlers-click-ai-bots-training/).

This unsustainable imbalance led to a radical response. In July 2025, Cloudflare announced it would block AI crawlers by default and launched ["Pay Per Crawl"](https://blog.cloudflare.com/introducing-pay-per-crawl/) — a solutin where publishers can charge AI companies for each page crawled. It's the first serious attempt to create a new business model for the AI era, where content isn't just consumed but compensated.  Here the current HTTP protcol is invoked, using an obscure HTTP access code 402 (as opposed to 404, 200 etc) indicating "Payment Required".

## The Human Question

What happens to humans in this new world? Beautiful showroom websites will likely remain—spaces for inspiration and brand experience. But the messy functionality—complex forms, comparison shopping, detailed research— could likely shift to AI agents working in the background.

Some companies are betting on the "everything app" approach. OpenAI and X.com seem to envision users never leaving their platforms, consuming all content through a single AI interface. It's Web 2.0's walled gardens taken to their logical extreme.

But human traffic is already dwarfed by bot traffic. How does this impact web analytics? E-commerce conversion rates? Media websites that survived on impression-based advertising now face an extinction-level event.

## The Privacy Revolution Returns

There's a twist in our story that harks back to Web 2.0's original promise: users controlling their own data.

What if individuals maintained their own A2A or MCP servers? All your purchase history, preferences, relationships, and interests in one place, under your control. You'd grant selective access to services in exchange for better experiences—verified, accurate profiles instead of the creepy tracking and guessing that defines today's web.

The protocols make this technically feasible today. The question is whether a post-GDPR population, increasingly aware of privacy violations, will demand it. Could user-controlled AI servers become the next revolution?

## What We've Learned

McKinsey found that only 1% of companies consider their AI deployment "mature" [AI in the workplace: A report for 2025 | McKinsey](https://www.mckinsey.com/capabilities/mckinsey-digital/our-insights/ai-in-the-workplace-a-report-for-2025). The other 99% are learning what we call the adaptability imperative: your AI infrastructure must evolve faster than AI itself.

MIT's research showing that purchasing specialized AI solutions succeeds 67% of the time versus 33% for internal builds [MIT report: 95% of generative AI pilots at companies are failing | Fortune](https://fortune.com/2025/01/15/ai-mit-research-generative-ai-productivity-technology/) isn't about capability—it's about learning curve. Vendors have already made the expensive mistakes.

At Sunholo, these aren't academic observations. Our Multivac platform emerged from seeing the same failures repeatedly: monolithic architectures that can't adapt, tightly coupled systems that break with every update, proprietary protocols that lock companies into obsolescence.

## The Inflection Point

We're witnessing the end of AI's wild west phase. Standards are emerging. The organizations recognizing this shift—building for tomorrow's pace of change rather than today's requirements—will define the next era.

The future isn't about having the best AI. It's about having AI that can collaborate with everyone else's AI, upgrade without breaking, experiment without committing, and respect user privacy and control.

The protocols are here. The early adopters are moving. The business models are being rewritten—from impression-based advertising to pay-per-crawl, from human web traffic to agent economies. The question isn't whether to embrace these standards, but whether you'll be part of the 5% that succeed or the 95% still trying to maintain custom integrations that were obsolete before they were finished.

History doesn't repeat, but it rhymes. The web's evolution from chaos to standards to walled gardens to user control is playing out again, just faster and with artificial minds as the primary actors.

Where does your organization fit in this story?

---

*Want to discuss how to navigate this transition? Reach out at multivac@sunholo.com or visit [www.sunholo.com](https://www.sunholo.com)*