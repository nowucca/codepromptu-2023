from typing import List
import re
import mimetypes
from core.models import Variable, Prompt, PromptCreate


class VariablesService:
    @staticmethod
    def is_valid_mime_type(mime_type: str) -> bool:
        # Use the mimetypes module to validate MIME types
        return bool(mimetypes.guess_extension(mime_type))

    @staticmethod
    def derive_variables(prompt: PromptCreate) -> None:
        # Calculate IO variables based on the updated prompt content
        io_variables = VariablesService.parse_io_variables(prompt.content)

        # Split variables into input and output
        input_variables, output_variables = VariablesService.split_variables_by_type(io_variables)

        # Update the prompt's input and output variables
        prompt.input_variables = input_variables
        prompt.output_variables = output_variables

    @staticmethod
    def split_variables_by_type(io_variables):
        """
        Split a list of IO variables into input and output variables based on their types.

        Args:
            io_variables (List[Variable]): List of IO variables.

        Returns:
            Tuple[List[Variable], List[Variable]]: A tuple containing input and output variables.
        """
        input_variables = []
        output_variables = []

        for variable in io_variables:
            if variable.type == "input":
                input_variables.append(variable)
            elif variable.type == "output":
                output_variables.append(variable)

        return input_variables, output_variables

    @staticmethod
    def parse_io_variables(content: str) -> List[Variable]:
        variables = []
        in_variable = False
        current_variable = {}
        current_token = ""
        open_braces = 0  # Track the number of open curly braces within a variable

        for char in content:
            if char == '{' and not in_variable:
                in_variable = True
                current_token = "{"
                open_braces = 1  # Initialize the count for the opening brace
            elif char == '}' and in_variable:
                current_token += "}"
                open_braces -= 1  # Decrease the count for the closing brace
                if open_braces == 0:
                    in_variable = False
                    try:
                        var_parts = current_token[1:-1].split(':')
                        var_name = var_parts[0].strip()
                        var_type = 'input'
                        var_format = 'text/plain'
                        var_description = ''

                        if var_name.endswith('!'):
                            var_type = 'output'
                            var_name = var_name.rstrip('!')

                        if len(var_parts) > 1:
                            var_format = var_parts[1].strip()

                        if len(var_parts) > 2:
                            # Remove escape sequences for {{ and }} within the description
                            var_description = var_parts[2].strip().replace('{{', '{').replace('}}', '}')

                        if not VariablesService.is_valid_mime_type(var_format):
                            raise ValueError(f"Invalid MIME type format: {var_format}")

                        if var_name not in current_variable:
                            variable = Variable(
                                name=var_name,
                                description=var_description,
                                type=var_type,
                                expected_format=var_format,
                            )
                            current_variable[var_name] = variable
                            variables.append(variable)
                    except Exception as e:
                        raise ValueError(f"Error parsing variable: {current_token}") from e
                    current_token = ""
            else:
                if in_variable:
                    current_token += char
                    if char == '{':
                        open_braces += 1

        return variables
