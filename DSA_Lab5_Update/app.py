import re

from flask import Flask, render_template, request

app = Flask(__name__)

INFIX_TOKEN_PATTERN = re.compile(
    r'\s*(\d+(?:\.\d*)?|\.\d+|[A-Za-z_][A-Za-z0-9_]*|[()+\-*/^])'
)


def infix_to_postfix(expression):
    tokens = []
    position = 0
    while position < len(expression):
        match = INFIX_TOKEN_PATTERN.match(expression, position)
        if not match:
            if expression[position:].strip():
                raise ValueError(f"Invalid character: '{expression[position]}'.")
            break
        tokens.append(match.group(1))
        position = match.end()

    if not tokens:
        raise ValueError('Enter an expression to convert.')

    precedence = {'+': 1, '-': 1, '*': 2, '/': 2, 'u+': 3, 'u-': 3, '^': 4}
    right_associative = {'^', 'u+', 'u-'}
    operators = []
    output = []
    expecting_operand = True

    for token in tokens:
        if re.fullmatch(r'\d+(?:\.\d*)?|\.\d+|[A-Za-z_][A-Za-z0-9_]*', token):
            if not expecting_operand:
                raise ValueError('Add an operator between operands.')
            output.append(token)
            expecting_operand = False
        elif token == '(':
            if not expecting_operand:
                raise ValueError("Add an operator before '('.")
            operators.append(token)
            expecting_operand = True
        elif token == ')':
            if expecting_operand:
                raise ValueError("Unexpected ')' or empty parentheses.")
            while operators and operators[-1] != '(':
                operator = operators.pop()
                output.append({'u+': 'POS', 'u-': 'NEG'}.get(operator, operator))
            if not operators:
                raise ValueError("Unmatched ')'.")
            operators.pop()
            expecting_operand = False
        else:
            if expecting_operand:
                if token in ('+', '-'):
                    operators.append('u' + token)
                    continue
                raise ValueError(f"Unexpected operator '{token}'.")

            while operators and operators[-1] != '(':
                top = operators[-1]
                if (precedence[top] > precedence[token]
                        or (precedence[top] == precedence[token]
                            and token not in right_associative)):
                    operator = operators.pop()
                    output.append({'u+': 'POS', 'u-': 'NEG'}.get(operator, operator))
                else:
                    break
            operators.append(token)
            expecting_operand = True

    if expecting_operand:
        raise ValueError('Expression cannot end with an operator.')

    while operators:
        operator = operators.pop()
        if operator == '(':
            raise ValueError("Unmatched '('.")
        output.append({'u+': 'POS', 'u-': 'NEG'}.get(operator, operator))

    return ' '.join(output)


def postfix_to_infix(expression):
    stripped_expression = expression.strip()
    if any(character.isspace() for character in stripped_expression):
        tokens = stripped_expression.split()
    else:
        tokens = list(stripped_expression)
    if not tokens:
        raise ValueError('Enter a postfix expression to convert.')

    operands = []
    binary_operators = {'+', '-', '*', '/', '^'}
    for token in tokens:
        if token in binary_operators:
            if len(operands) < 2:
                raise ValueError(f"Not enough operands for '{token}'.")
            right = operands.pop()
            left = operands.pop()
            operands.append(f'({left} {token} {right})')
        elif token in ('NEG', 'POS'):
            if not operands:
                raise ValueError(f"Not enough operands for '{token}'.")
            operand = operands.pop()
            sign = '-' if token == 'NEG' else '+'
            operands.append(f'({sign}{operand})')
        elif re.fullmatch(r'\d+(?:\.\d*)?|\.\d+|[A-Za-z_][A-Za-z0-9_]*', token):
            operands.append(token)
        else:
            raise ValueError(f"Invalid token: '{token}'.")

    if len(operands) != 1:
        raise ValueError('The postfix expression has too many operands or is missing an operator.')

    return operands[0]


def parse_linked_list_values(raw_values):
    if not raw_values:
        return []
    values = []
    for item in raw_values.split(','):
        value = item.strip()
        if value:
            values.append(value)
    return values


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/profile')
def profile():
    return render_template('profile.html')


@app.route('/works', methods=['GET', 'POST'])
def works():
    if request.method == 'POST':
        input_string = request.form.get('inputString', '')
        result = input_string.upper()
        return render_template('touppercase.html', result=result)
    return render_template('works.html')


@app.route('/works/uppercase', methods=['GET', 'POST'])
def uppercase():
    result = None
    if request.method == 'POST':
        input_string = request.form.get('inputString', '')
        result = input_string.upper()
    return render_template('touppercase.html', result=result)


@app.route('/works/expression-converter', methods=['GET', 'POST'])
def expression_converter():
    infix_expression = ''
    postfix_expression = ''
    conversion = None
    result = None
    error = None

    if request.method == 'POST':
        conversion = request.form.get('conversion', '')
        infix_expression = request.form.get('infix_expression', '')
        postfix_expression = request.form.get('postfix_expression', '')

        try:
            if conversion == 'infix_to_postfix':
                result = infix_to_postfix(infix_expression)
            elif conversion == 'postfix_to_infix':
                result = postfix_to_infix(postfix_expression)
            else:
                error = 'Choose a conversion direction.'
        except ValueError as exc:
            error = str(exc)

    return render_template(
        'expression_converter.html',
        infix_expression=infix_expression,
        postfix_expression=postfix_expression,
        conversion=conversion,
        result=result,
        error=error,
    )


@app.route('/works/linked-list', methods=['GET', 'POST'])
def linked_list():
    values = []
    operation = 'insert_end'
    message = None
    show_list = False

    if request.method == 'POST':
        show_list = True
        raw_values = request.form.get('values', '')
        values = parse_linked_list_values(raw_values)
        operation = request.form.get('operation', 'insert_end')
        new_value = request.form.get('new_value', '').strip()

        if operation in ('insert_beginning', 'prepend') and new_value:
            values.insert(0, new_value)
        elif operation in ('insert_end', 'append') and new_value:
            values.append(new_value)
        elif operation == 'remove_beginning':
            if values:
                values.pop(0)
            else:
                message = 'The list is empty; there is no node to remove.'
        elif operation == 'remove_end':
            if values:
                values.pop()
            else:
                message = 'The list is empty; there is no node to remove.'
        elif operation == 'insert':
            if not new_value:
                message = 'Enter a value to insert.'
            else:
                try:
                    index = int(request.form.get('index', '0').strip())
                except ValueError:
                    message = 'Enter a whole-number position.'
                else:
                    if 0 <= index <= len(values):
                        values.insert(index, new_value)
                    else:
                        message = f'Insert position must be between 0 and {len(values)}.'
        elif operation == 'remove_position':
            try:
                index = int(request.form.get('index', '0').strip())
            except ValueError:
                message = 'Enter a whole-number position.'
            else:
                if 0 <= index < len(values):
                    values.pop(index)
                else:
                    message = f'Remove position must be between 0 and {len(values) - 1}.'
        elif operation not in ('insert_beginning', 'prepend', 'insert_end', 'append'):
            message = 'Choose a valid linked-list operation.'
        elif not new_value:
            message = 'Enter a value to insert.'

    return render_template(
        'linked_list.html',
        values=values,
        show_list=show_list,
        operation=operation,
        message=message,
    )


@app.route('/works/area/circle', methods=['GET', 'POST'])
def acircle():
    result = None
    if request.method == 'POST':
        radius = request.form.get('radius', '')
        result = int(radius)*3.14*int(radius)
    return render_template('circle.html', result=result)


@app.route('/works/area/triangle', methods=['GET', 'POST'])
def atriangle():
    result = None
    if request.method == 'POST':
        base = request.form.get('base', '')
        height = request.form.get('height', '')
        if base and height:
            result = float(base) * float(height) / 2
    return render_template('triangle.html', result=result)


# @app.route('/areaOfcirle', methods=['GET', 'POST'])
# def areaOfcirle():
#     result = None
#     name=request.get('name','')
#     print(name)
#     if request.method == 'POST':
#         input_string = request.form.get('inputradius', '')
#         result = int(input_string) * int(input_string) * 3.14
#     return render_template('areaCircle.html', result=result)


@app.route('/contact')
def contact():
    return render_template('contact.html')


if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)
