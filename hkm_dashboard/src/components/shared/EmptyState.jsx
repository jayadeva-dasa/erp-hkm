import { Box, Heading, Text, VStack } from '@chakra-ui/react';

const EmptyState = ({ title = 'No data available', description }) => (
  <Box px={{ base: 4, md: 10 }} py={12}>
    <VStack spacing={3} align="center">
      <Heading size="md" color="gray.600">
        {title}
      </Heading>
      {description && (
        <Text color="gray.500" textAlign="center" maxW="xl">
          {description}
        </Text>
      )}
    </VStack>
  </Box>
);

export default EmptyState;

