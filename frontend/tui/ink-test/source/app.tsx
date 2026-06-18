import {Box, Text, useApp, useInput} from 'ink';
import React, {FC, useEffect, useState} from 'react';

interface IProps {
  items: string[];
}

const App: FC<IProps> = ({items}) => {
  const [choice, setChoice] = useState(0);
  const [isSelected, setIsSelected] = useState(false);
  const {exit} = useApp();

  useInput((_, key) => {
    if (key.upArrow) {
      setChoice(prev => (prev > 0 ? prev - 1 : 0));
    } else if (key.downArrow) {
      setChoice(prev => (prev < items.length - 1 ? prev + 1 : prev));
    } else if (key.return) {
      setIsSelected(true);
    }
  });

  useEffect(() => {
    if (isSelected || items.length === 0) exit();
  }, [exit, isSelected, items]);

  if (items.length <= 0) {
    return <Text color={'red'}>缺少参数</Text>;
  }

  return (
    <Box flexDirection="column">
      <Text>请选择一个选项</Text>
      {items.map((choiceText, index) => (
        <Text
          key={`${choiceText}-${index}`}
          color={choice === index ? 'green' : undefined}
        >
          {choice === index ? '> ' : '  '}
          {choiceText}
        </Text>
      ))}
      {isSelected && <Text color={'yellow'}>你选择了：{items[choice]}</Text>}
    </Box>
  );
};

export default App;
