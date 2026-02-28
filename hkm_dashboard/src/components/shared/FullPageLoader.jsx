import { Center, Spinner, Text, VStack } from '@chakra-ui/react';

const FullPageLoader = ({ label = 'Loading data...' }) => (
  <Center minH="60vh">
    <VStack spacing={4}>
      <Spinner size="xl" color="orange.400" thickness="4px" speed="0.8s" />
      <Text color="gray.500">{label}</Text>
    </VStack>
  </Center>
);

export default FullPageLoader;

