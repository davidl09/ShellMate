import subprocess
import uuid
from os import getenv

print("Warning: This file has been deprecated")

class CommandError(Exception):
    def __init__(self, message, exit_code):
        super().__init__(message)
        self.exit_code = exit_code
        self.output = message

class CommandExecutor:
    def __init__(self):
        shell = getenv('SHELL') or 'bash'
        self.marker = str(uuid.uuid4())
        self.process = subprocess.Popen(
            [shell, '--norc', '-s'],  # Start non-interactive shell in silent mode
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self._initialize_shell()

    def _initialize_shell(self):
        """Set up shell environment and verify working connection."""
        init_commands = [
            'PS1=',  # Disable prompt
            'PS2=',  # Disable continuation prompt
            'set +o history',  # Disable command history
            f'echo "{self.marker}"'  # Produce initial marker
        ]
        for cmd in init_commands:
            self.process.stdin.write(cmd + '\n')
        self.process.stdin.flush()
        self._read_until_marker()

    def _read_until_marker(self):
        """Read output until marker is found, discarding previous content."""
        while True:
            line = self.process.stdout.readline()
            if not line:
                raise RuntimeError("Shell process terminated unexpectedly")
            if line.strip() == self.marker:
                return

    def execute_command(self, command):
        """Execute a shell command and return its output or raise CommandError."""
        # Format command to capture output and exit status, without subshell
        wrapped_command = (
            f'{command} 2>&1\n'  # Execute command with stderr redirection
            f'echo "{self.marker}:$?"\n'  # Marker with exit code
        )
        
        try:
            self.process.stdin.write(wrapped_command)
            self.process.stdin.flush()
        except BrokenPipeError:
            raise RuntimeError("Shell process terminated unexpectedly")

        output = []
        exit_code = None
        while True:
            line = self.process.stdout.readline()
            if not line:
                break
            
            line = line.rstrip('\n')
            # Check if this is our marker line with exit code
            if line.startswith(f'{self.marker}:'):
                try:
                    exit_code = int(line.split(':')[1])
                except (IndexError, ValueError):
                    exit_code = -1
                break
            output.append(line)

        if exit_code is None:
            raise RuntimeError("Failed to capture command exit code")

        full_output = '\n'.join(output)
        if exit_code != 0:
            raise CommandError(full_output, exit_code)
        return full_output

    def __del__(self):
        if hasattr(self, 'process') and self.process.poll() is None:
            self.process.stdin.close()
            self.process.terminate()
            self.process.wait()

if __name__ == "__main__":
    def run_tests(executor):
        tests_passed = 0
        total_tests = 0
        
        def assert_test(condition, test_name):
            nonlocal tests_passed, total_tests
            total_tests += 1
            if condition:
                tests_passed += 1
                print(f"✓ {test_name}")
            else:
                print(f"✗ {test_name}")
        
        # Test 1: Basic command execution
        try:
            output = executor.execute_command("echo 'test'")
            assert_test(output == "test", "Basic command execution")
        except Exception as e:
            assert_test(False, f"Basic command execution (failed with {str(e)})")

        # Test 2: Directory persistence
        try:
            executor.execute_command("cd /tmp")
            output = executor.execute_command("pwd")
            assert_test(output == "/tmp", "Directory persistence")
        except Exception as e:
            assert_test(False, f"Directory persistence (failed with {str(e)})")

        # Test 3: Multiple command execution
        try:
            output = executor.execute_command("echo 'hello' && echo 'world'")
            assert_test(output == "hello\nworld", "Multiple command execution")
        except Exception as e:
            assert_test(False, f"Multiple command execution (failed with {str(e)})")

        # Test 4: Command with stderr
        try:
            output = executor.execute_command("ls /nonexistent 2>&1")
            assert_test(False, "Command with stderr should fail")
        except CommandError as e:
            assert_test("No such file or directory" in e.output, "Command with stderr error message")

        # Test 5: Environment variable persistence
        try:
            executor.execute_command("export TEST_VAR='hello'")
            output = executor.execute_command("echo $TEST_VAR")
            assert_test(output == "hello", "Environment variable persistence")
        except Exception as e:
            assert_test(False, f"Environment variable persistence (failed with {str(e)})")

        # Test 6: Command with spaces and special characters
        try:
            output = executor.execute_command("echo 'hello   world!\n\"test\"'")
            assert_test(output == "hello   world!\n\"test\"", "Special characters handling")
        except Exception as e:
            assert_test(False, f"Special characters handling (failed with {str(e)})")

        # Test 7: Pipeline commands
        try:
            output = executor.execute_command("echo 'hello\nworld' | grep 'world'")
            assert_test(output == "world", "Pipeline command execution")
        except Exception as e:
            assert_test(False, f"Pipeline command execution (failed with {str(e)})")

        # Test 8: Empty command
        try:
            output = executor.execute_command("")
            assert_test(output == "", "Empty command handling")
        except Exception as e:
            assert_test(False, f"Empty command handling (failed with {str(e)})")

        # Test 9: Long output handling
        try:
            output = executor.execute_command("for i in {1..100}; do echo $i; done")
            lines = output.split('\n')
            assert_test(len(lines) == 100 and lines[0] == "1" and lines[-1] == "100", 
                       "Long output handling")
        except Exception as e:
            assert_test(False, f"Long output handling (failed with {str(e)})")

        # Test 10: Command substitution
        try:
            output = executor.execute_command("echo $(echo 'nested command')")
            assert_test(output == "nested command", "Command substitution")
        except Exception as e:
            assert_test(False, f"Command substitution (failed with {str(e)})")
        
        # Test 11: Sudo
        try:
            output = executor.execute_command("sudo echo 'test'")
            assert_test(output == "test", "Sudo command execution")
        except Exception as e:
            assert_test(False, f"Sudo command execution (failed with {str(e)})")

        # Print test summary
        print(f"\nTests completed: {tests_passed}/{total_tests} passed")
        return tests_passed == total_tests
    
    # Run all tests
    # commands = [
    #     "vim test.txt",
    #     "i", 
    #     "hello world!",
    #     "\x1B",
    #     ":wq",
    #     "cat test.txt",
    #     "exit"
    # ]
    # executor = CommandExecutor()
    # for command in commands:
    #     try:
    #         result = executor.execute_command(command)
    #         print(f"Command '{command}' succeded: '{result}'")
    #     except:
    #         print(f"Command '{command}' failed")
    # del executor
    executor = CommandExecutor()
    
    try:
        success = run_tests(executor)
        print("\nAll tests passed!" if success else "\nSome tests failed!")
    except Exception as e:
        print(f"\nTest suite failed with error: {str(e)}")
    finally:
        del executor
    