export type GreetingOptions = {
  name: string;
};

export function createGreeting(options: GreetingOptions): string {
  const { name } = options;
  const trimmedName = name.trim();
  if (!trimmedName) {
    throw new Error('Name is required for greeting.');
  }
  return `Hello, ${trimmedName}!`;
}
