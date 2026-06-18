#!/usr/bin/env node
import React from 'react';
import {render} from 'ink';
import App from './app.js';
import meow from 'meow';

const cli = meow(
  // 这个是帮助文本内容 用户加上 --help 参数的时候会展示这些文本
  `
  Usage
    $ ink-test <选项...>

  Examples
    $ ink-test 苹果 香蕉 橙子
  `,
  {
    // 必须传递，否则读取不到版本号
    importMeta: import.meta,
  },
);

let selected: string | undefined;

const {waitUntilExit} = render(
  <App
    items={cli.input}
    onSelected={val => {
      selected = val;
    }}
  />,
  {
    stdout: process.stderr,
  },
);
await waitUntilExit();
if (selected) console.log(selected);
