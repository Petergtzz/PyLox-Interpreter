# interpreter.py

from expr import NodeVisitor
from error_handler import ErrorHandler
from collections import ChainMap

class Interpreter(NodeVisitor):
    '''
    This class traverses through a syntax tree 
    '''
    def __init__(self):
        self.error_handler = ErrorHandler()
        self.env = ChainMap()
        
    def interpret(self, node):
        try: 
            for stmt in node:
                self.visit(stmt)
        except RuntimeError as error:
            self.error_handler.runtime_error(error)

    def check_numeric_operands(self, node, left, right):
        if isinstance(left, float) and isinstance(right, float):
            return True
        else: 
            self.error_handler.error(node, 'operands must be numbers')
    
    def check_numeric_operand(self, node, value):
        if isinstance(value, float):
            return True
        else:
            self.error_handler.error(node, 'operand must be a number')

    def execute_Block(self, node, env):
        previous = self.env
        try:
            self.env = env
            for stmt in node: 
                self.visit(stmt)
        finally:
            self.env = previous

    def visit_Literal(self, node):
        return node.value
    
    def visit_Logical(self, node):
        left = self.visit(node.left)

        if node.op.lexeme == 'or':
            return left if self.is_truthy(left) else self.visit(node.right)
        if node.op.lexeme == 'and':
            return self.visit(node.right) if self.is_truthy(left) else left
                
    def visit_Grouping(self, node):
        return self.visit(node.value)
    
    def visit_Unary(self, node):
        right = self.visit(node.right)

        if node.op.lexeme == '-':
            self.check_numeric_operand(node, right)
            return -right
        elif node.op.lexeme == '!':
            return not self.is_truthy(right)
        else: 
            raise NotImplementedError(f'Bad operator {node.op}')
        
    def visit_Variable(self, node):
        return self.env.get(node.name.lexeme)
    
    def visit_WhileStmt(self, node):
        while self.is_truthy(self.visit(node.test)):
            self.visit(node.body)
        
    def visit_Binary(self, node):
        left = self.visit(node.left)
        right = self.visit(node.right)

        operator = node.op.lexeme
        match operator:
            case '-':
                self.check_numeric_operands(node, left, right)
                return left - right
            case '/':
                try:
                    self.check_numeric_operands(node, left, right)
                    return left / right
                except ZeroDivisionError as error:
                    print('ZeroDivisionError:', error)
            case '*':
                self.check_numeric_operands(node, left, right)
                return left * right
            case '+':
                (isinstance(left, str) and isinstance(right, str)) or self.check_numeric_operands(node, left, right)
                return left + right 
            case '>':
                self.check_numeric_operands(node, left, right)
                return left > right
            case '>=':
                self.check_numeric_operands(node, left, right)
                return left >= right
            case '<':
                self.check_numeric_operands(node, left, right)
                return left < right
            case '<=':
                self.check_numeric_operands(node, left, right)
                return left <= right
            case '!=':
                return not self.is_equal(left, right)
            case '==':
                return self.is_equal(left, right)
            
     # TODO: Check if return in valid       
    def visit_ExprStmt(self, node):
        self.visit(node.value)

    def visit_IfStmt(self, node):
        if self.is_truthy(self.visit(node.test)):
            self.visit(node.consequence)
        elif node.alternative:
            self.visit(node.alternative)
    
    def visit_Print(self, node):
        value = self.visit(node.value)
        print(self.stringify(value))

    def visit_VarDeclaration(self, node):
        if node.initializer:
            initializer = self.visit(node.initializer)
        else:
            initializer = None

        self.env[node.name.lexeme] = initializer

    # IMPORTANT: Check for runtime errors
    def visit_Assign(self, node):
        value = self.visit(node.value)
        self.env[node.name.lexeme] = value
        return value 
    
    def visit_Block(self, node):
        self.execute_Block(node.statements, self.env.new_child())
 
    def is_truthy(self, value):
        # Logic to decide what happens when you use something other than true or false
        if value is None:
            return False
        elif isinstance(value, bool):
            return value
        else:
            return True
        
    def is_equal(self, a, b):
        if a is None and b is None:
            return True
        elif a is None:
            return False
        return a.__eq__(b)
    
    def stringify(self, value):
        # Converts the expression result value to a string 
        if value is None:
            return 'nil'
        elif isinstance(value, float):
            text = str(value)
            if text.endswith('.0'):
                text = text[0:len(text) - 2]
            return text
        return str(value)
    
def test_interpreter():
    from parse import Parser
    from scanner import Scanner
    
    def interpret(source):
        interpreter = Interpreter()
        scanner = Scanner(source, ErrorHandler())
        parser = Parser(scanner.scan_tokens(), ErrorHandler())
        expression = parser.parse()
        return interpreter.interpret(expression)

    #assert interpret('-2+3;') == '1'
    #assert interpret('2+3*4;') == '14'
    #assert interpret('2*3+4;') == '10'
    #assert interpret('2+3 < 4+5;') == 'True'
    #assert interpret('2 < 3 == 4 < 5;') == 'True'
    #assert interpret('(2+3)*4;') == '20' 
    #assert interpret('print true;') == True
    #assert interpret('print 2 + 1;') == 3
    #interpret('print (2 * 3);')
    #interpret("var a = 1;\nvar b = 2;\nprint a + b;")
    #interpret("var a = 1;\nprint a = 2;")
    #interpret('var a = "global a";\n'
    #          'var b = "global b";\n'
    #          'var c = "global c";\n'
    #          '{\n'
    #          '  var a = "outer a";\n'
    #          '  var b = "outer b";\n'
    #          '  {\n'
    #          '    var a = "inner a";\n'
    #          '    print a;\n'
    #          '    print b;\n'
    #          '    print c;\n'
    #          '  }\n'  
    #          '  print a;\n'
    #          '  print b;\n'
    #          '  print c;\n'
    #          '}\n'
    #          'print a;\n'
    #          'print b;\n'
    #          'print c;')
    #interpret('print nil or "yes";')
    interpret('var a = 0;\n'
              'var temp;\n'
              'for (var b = 1; a < 10000; b = temp + b) {\n'
              'print a;\n'
              'temp = a;\n'
              'a = b;\n'
              '}')
    #interpret("var b = 2;")
    #interpret("print a + b;")
    #print('Good tests!')
    
#test_interpreter()
        

