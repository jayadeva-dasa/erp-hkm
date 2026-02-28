import { Alert, AlertIcon, AlertTitle, AlertDescription, Box } from '@chakra-ui/react';

const ErrorState = ({ title = 'Something went wrong', description }) => (
  <Box px={{ base: 4, md: 10 }} py={6}>
    <Alert status="error" borderRadius="lg" variant="subtle">
      <AlertIcon />
      <Box>
        <AlertTitle>{title}</AlertTitle>
        {description && <AlertDescription>{description}</AlertDescription>}
      </Box>
    </Alert>
  </Box>
);

export default ErrorState;

