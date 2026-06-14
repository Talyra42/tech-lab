import {Box, Spacer, Text} from 'ink';
import React, {useEffect, useState} from 'react';

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
      <Box borderStyle={'round'} width={20}>
        <Text>Counter</Text>
        <Spacer />
        <Text>{counter}</Text>
      </Box>
    </>
  );
}
