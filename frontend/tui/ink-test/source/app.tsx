import {Box, Text, useApp, useInput} from 'ink';
import React, {useState} from 'react';

const CHOICES = ['苹果', '香蕉', '橙子'];

export default function App() {
  const [choice, setChoice] = useState(0);
  const [isSelected, setIsSelected] = useState(false);
  const {exit} = useApp();

  useInput((_, key) => {
    if (key.upArrow) {
      setChoice(prev => (prev > 0 ? prev - 1 : 0));
    } else if (key.downArrow) {
      setChoice(prev => (prev < CHOICES.length - 1 ? prev + 1 : prev));
    } else if (key.return) {
      setIsSelected(true);
      setTimeout(() => {
        exit();
      }, 0);
    }
  });

  return (
    <Box flexDirection="column">
      <Text>请选择一个选项</Text>
      {CHOICES.map((choiceText, index) => (
        <Text key={choiceText} color={choice === index ? 'green' : undefined}>
          {choice === index ? '> ' : '  '}
          {choiceText}
        </Text>
      ))}
      {isSelected && <Text color={'yellow'}>你选择了：{CHOICES[choice]}</Text>}
    </Box>
  );
}
