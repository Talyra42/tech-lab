import {Box, Spacer, Text} from 'ink';
import React, {useEffect, useState} from 'react';
import {TextInput} from '@inkjs/ui';

export default function App() {
  const [counter, setCounter] = useState(0);

  useEffect(() => {
    let timer = setInterval(() => {
      setCounter(prev => prev + 1);
    }, 100);

    return () => clearInterval(timer);
  }, []);

  return (
    <>
      <Box flexDirection="column" borderStyle={'round'} gap={2}>
        <Box width={20}>
          <Text>Counter</Text>
          <Spacer />
          <Text>{counter}</Text>
        </Box>
        <Box flexDirection="column">
          <Text>模拟登录表单</Text>
          <TextInput placeholder="输入用户名"></TextInput>
        </Box>
      </Box>
    </>
  );
}
