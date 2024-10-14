// @ts-check
// `@type` JSDoc annotations allow editor autocompletion and type checking
// (when paired with `@ts-check`).
// There are various equivalent ways to declare your Docusaurus config.
// See: https://docusaurus.io/docs/api/docusaurus-config

import {themes as prismThemes} from 'prism-react-renderer';
import proxyMiddleware from './src/plugins/proxy';

import 'dotenv/config';

/** @type {import('@docusaurus/types').Config} */

const config = {
  customFields: {
    // Put your custom environment here
    multivacApiKey: process.env.REACT_APP_MULTIVAC_API_KEY || 'default_key_if_not_defined',
  },
  title: 'Sunholo Dev Portal',
  tagline: 'Development resources for Sunholo and Multivac',
  favicon: 'img/favicon.ico',

  // Set the production url of your site here
  url: 'https://dev.sunholo.com',
  // Set the /<baseUrl>/ pathname under which your site is served
  // For GitHub pages deployment, it is often '/<projectName>/'
  baseUrl: '/',

  // GitHub pages deployment config.
  // If you aren't using GitHub pages, you don't need these.
  organizationName: 'sunholo-data', // Usually your GitHub org/user name.
  projectName: 'sunholo-py', // Usually your repo name.

  onBrokenLinks: 'throw',
  onBrokenMarkdownLinks: 'warn',

  // Even if you don't use internationalization, you can use this field to set
  // useful metadata like html lang. For example, if your site is Chinese, you
  // may want to replace "en" with "zh-Hans".
  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
      'classic',
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          sidebarPath: './sidebars.js',
          // Please change this to your repo.
          // Remove this to remove the "edit this page" links.
          editUrl:
            'https://github.com/sunholo-data/sunholo-py/tree/main/docs/',
        },
        //blog: true,
        blog: {
        //  showReadingTime: true,
          // Please change this to your repo.
          // Remove this to remove the "edit this page" links.
          //editUrl: null,
        },
        googleTagManager: {
          containerId: 'GTM-WLQZQF2P',
        },
        theme: {
          customCss: './src/css/custom.css',
        },
      }),
    ],
  ],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      // Replace with your project's social card
      image: 'img/docusaurus-social-card.jpg',
      navbar: {
        title: 'Sunholo',
        logo: {
          alt: 'Sunholo Logo',
          src: 'img/eclipse1.png',
        },
        items: [
          {
            type: 'docSidebar',
            sidebarId: 'tutorialSidebar',
            position: 'left',
            label: 'Documentation',
          },
          {to: '/blog', label: 'Blog', position: 'left'},
          {
            href: 'https://github.com/sunholo-data/sunholo-py',
            label: 'GitHub',
            position: 'right',
          },
          {
            href: 'https://www.sunholo.com',
            label: 'Multivac',
            position: 'right',
          },
        ],
      },
      footer: {
        style: 'dark',
        links: [
          {
            title: 'Docs',
            items: [
              {
                label: 'Tutorial',
                to: '/',
              },
            ],
          },
          {
            title: 'Community',
            items: [
              {
                label: 'Discord',
                href: 'https://discord.gg/RANn65Rh9a',
              },
            ],
          },
          {
            title: 'More',
            items: [
              {
                label: 'Blog',
                to: '/blog',
              },
              {
                label: 'GitHub',
                href: 'https://github.com/sunholo-data/sunholo-py',
              },
            ],
          },
        ],
        copyright: `Copyright © ${new Date().getFullYear()} Holosun ApS`,
      },
      prism: {
        theme: prismThemes.github,
        darkTheme: prismThemes.dracula,
      },
    }),

    

  plugins: [
    './src/plugins/proxy',
    [
      
      '@docusaurus/plugin-ideal-image',
      {
        quality: 70,
        max: 1030, // max resized image's size.
        min: 640, // min resized image's size. if original is lower, use that size.
        steps: 2, // the max number of images generated between min and max (inclusive)
        disableInDev: false,
      },
    ],
  ],
};

export default config;
