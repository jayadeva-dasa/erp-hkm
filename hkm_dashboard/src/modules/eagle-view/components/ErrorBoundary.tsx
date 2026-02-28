import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Box, Text, Button, VStack, Code } from '@chakra-ui/react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
    errorInfo: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error, errorInfo: null };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    this.setState({
      error,
      errorInfo,
    });
  }

  private handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  public render() {
    if (this.state.hasError) {
      return (
        <Box p={6} bg="red.50" borderRadius="lg" border="1px" borderColor="red.200">
          <VStack spacing={4} align="stretch">
            <Text fontSize="xl" fontWeight="bold" color="red.600">
              Something went wrong
            </Text>
            <Text color="gray.700">
              An error occurred while rendering the report. Please check the console for details.
            </Text>
            {this.state.error && (
              <Box bg="white" p={4} borderRadius="md" border="1px" borderColor="red.200">
                <Text fontWeight="semibold" mb={2}>Error:</Text>
                <Code colorScheme="red" p={2} display="block" whiteSpace="pre-wrap">
                  {this.state.error.toString()}
                </Code>
              </Box>
            )}
            {this.state.errorInfo && (
              <Box bg="white" p={4} borderRadius="md" border="1px" borderColor="red.200">
                <Text fontWeight="semibold" mb={2}>Component Stack:</Text>
                <Code colorScheme="red" p={2} display="block" whiteSpace="pre-wrap" fontSize="xs">
                  {this.state.errorInfo.componentStack}
                </Code>
              </Box>
            )}
            <Button colorScheme="red" onClick={this.handleReset}>
              Try Again
            </Button>
          </VStack>
        </Box>
      );
    }

    return this.props.children;
  }
}

