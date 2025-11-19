from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from .services import SQLAgent


def query_form(request):
    """Main query form page"""
    return render(request, 'querycraft/query_form.html')


@csrf_exempt
@require_http_methods(["POST"])
def process_query(request):
    """Process question and return result"""
    try:
        data = json.loads(request.body)
        question = data.get('question', '').strip()
        
        if not question:
            return JsonResponse({
                'success': False,
                'error': 'Please enter a question'
            })
        
        # Use AI Agent to convert to SQL
        agent = SQLAgent()
        sql_result = agent.generate_sql(question)
        
        if sql_result.get('error'):
            return JsonResponse({
                'success': False,
                'error': f"Error generating SQL: {sql_result['error']}",
                'question': question
            })
        
        sql_query = sql_result.get('sql')
        if not sql_query:
            return JsonResponse({
                'success': False,
                'error': 'Could not generate appropriate SQL',
                'question': question
            })
        
        # Execute query
        execution_result = agent.execute_query(sql_query)
        
        return JsonResponse({
            'success': execution_result.get('success', False),
            'question': question,
            'sql_query': sql_query,
            'method': sql_result.get('method', 'unknown'),
            'results': execution_result.get('results', []),
            'row_count': execution_result.get('row_count', 0),
            'columns': execution_result.get('columns', []),
            'error': execution_result.get('error'),
        })
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Error processing request'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error: {str(e)}'
        })

