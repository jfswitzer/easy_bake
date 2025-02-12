#define _GNU_SOURCE
#include <fcntl.h>
#include <curses.h>
#include <immintrin.h>
#include <limits.h>
#include <pthread.h>
#include <sched.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <x86intrin.h>

int verbose=1;
int fd;
int faulty_result_found=0;
int undervolting_finished=0;
uint64_t plane0_zero;
uint64_t plane2_zero;

typedef struct calculation_info_t
{
	char max_or_fixed_op1;
	char max_or_fixed_op2;
	uint64_t operand1;
	uint64_t operand2;
	uint64_t operand1_min;
	uint64_t operand2_min;
	uint64_t correct_a;
	uint64_t correct_b;
	uint64_t iterations_performed;
	int thread_number;
} calculation_info;

void *multiply_it(void *input)
{
	calculation_info *ci=(calculation_info*)input;
	uint64_t iterations=ci->iterations_performed;
	uint64_t max1=ci->operand1;
	uint64_t max2=ci->operand2;
	uint64_t min1=ci->operand1_min;
	uint64_t min2=ci->operand2_min;
	unsigned int one,two;
	while (faulty_result_found==0 && undervolting_finished==0)
	{
		ci->iterations_performed=0;
		if (ci->max_or_fixed_op1=='M')
		{
			__builtin_ia32_rdrand32_step(&one);
			ci->operand1=one % (max1 - min1) + min1;
		}
		if (ci->max_or_fixed_op2=='M')
		{
			__builtin_ia32_rdrand32_step(&two);
			ci->operand2=(two % (max2-min2)) + 1+min2 ;
		}
		do
		{
		  ci->iterations_performed++;
		  ci->correct_a = ci->operand1 * ci->operand2;
		  ci->correct_b = ci->operand1 * ci->operand2;
		} while (ci->correct_a==ci->correct_b && 
                         ci->iterations_performed<iterations && 
			 faulty_result_found==0 &&
			 undervolting_finished==0);
	
		if (ci->correct_a!=ci->correct_b && faulty_result_found==0)
		{
			faulty_result_found=1;
		}
	}
	return NULL;
}

void *undervolt_it(void *input) {
  return NULL;
}
void usage(const char* program)
{
	printf("\t -i #           \t iterations\n");
	printf("\t -1 0x#         \t operand1\n");
	printf("\t -2 0x#         \t operand2\n");
	printf("\t -t #           \t number of threads - default=1\n");
	printf("\t -z fixed | max \t fixed|max (what is operand 1 - default=fixed)\n");
	printf("\t -x fixed | max \t fixed|max (what is operand 2 - default=fixed)\n");
	printf("\t -q #           \t operand 1 minimum - default=0\n");
	printf("\t -w #           \t operand 2 minimum - default=0\n");
	printf("\t -S             \t Silent mode - default=verbose\n");
	printf("\t -h             \t display this Help\n");

}
int main (int argc, char* argv[])
{
	const char* program=argv[0];
	if (argc < 2 )
	{
		usage(program);
		return -1;
	}
	uint64_t iterations = 1000;
	uint64_t operand1=4294967296, operand2=4294967296;
	char max_or_fixed_op1='M', max_or_fixed_op2='M';
	uint64_t operand1_min=0,operand2_min=0;
	int number_of_threads=1;
	int opt=0;

    while((opt = getopt(argc, argv, ":e:i:s:v:t:1:2:q:w:X:z:x:SMCh")) != -1)  
    {  
        switch(opt)  
        {  
	    case '1':
		operand1=strtol(optarg,NULL,16);
		break;
	    case '2':
		operand2=strtol(optarg,NULL,16);
		break;
            case 'z':
		if (strcmp(optarg,"fixed")==0)
			max_or_fixed_op1='F';
		else if (strcmp(optarg,"max")==0)
			max_or_fixed_op1='M';
		else
		{
			printf ("Error setting operand1 to be fixed or max value\n");
			return -1;
		}
                break;  
            case 'x':
		if (strcmp(optarg,"fixed")==0)
			max_or_fixed_op2='F';
		else if (strcmp(optarg,"max")==0)
			max_or_fixed_op2='M';
		else
		{
			printf ("Error setting operand2 to be fixed or max value\n");
			return -1;
		}
                break;  
	    case 'i':
	        iterations = strtol(optarg,NULL,10);
		break;
	    case 'h':
	        usage(program);
		return -1;
            case 'q':  
		operand1_min=strtol(optarg,NULL,16);
                break;  
            case 'w':  
		operand2_min=strtol(optarg,NULL,16);
                break;  
            case 't':  
		number_of_threads=strtol(optarg,NULL,10);
                break;    
            case 'S':  
		verbose=0;
                break;  
            case ':':  
                printf("option needs a value\n");  
                break;  
            case '?':  
                printf("unknown option: %c\n", optopt); 
                break;  
        }  
    }  
	if (verbose)
	{
		printf("\r\nSummary\n");
		printf("\r-------------------------------------------------\n");
		printf("\rIterations:          %li\n",iterations);
		printf("\rThreads:             %i\n",number_of_threads);
		printf("\rOperand1:            0x%016lx\n",operand1);
		printf("\rOperand2:            0x%016lx\n",operand2);
		printf("\rOperand1 is:         %s\n",max_or_fixed_op1=='M'?"maximum":"fixed value");
		printf("\rOperand2 is:         %s\n",max_or_fixed_op2=='M'?"maximum":"fixed value");
		printf("\rOperand1 min is:     0x%016lx\n",operand1_min);
		printf("\rOperand2 min is:     0x%016lx\n",operand2_min);
	}

	pthread_t* my_calculation_thread=malloc(sizeof(pthread_t)*number_of_threads);
	calculation_info* calculation_data=malloc(sizeof(calculation_info)*number_of_threads);


	for (int i=0;i<number_of_threads;i++)
	{
		calculation_data[i].operand1=operand1;
		calculation_data[i].operand2=operand2;
		calculation_data[i].operand1_min=operand1_min;
		calculation_data[i].operand2_min=operand2_min;
		calculation_data[i].max_or_fixed_op1=max_or_fixed_op1;
		calculation_data[i].max_or_fixed_op2=max_or_fixed_op2;
		calculation_data[i].correct_a=0;
		calculation_data[i].correct_b=0;
		calculation_data[i].iterations_performed=iterations;
		calculation_data[i].thread_number=i;
		pthread_create(&my_calculation_thread[i], NULL, multiply_it, &calculation_data[i]);
	}

	for (int i=0;i<number_of_threads;i++)
	{
    		pthread_join(my_calculation_thread[i], NULL);
	}

	for (int i=0;i<number_of_threads;i++)
	{
		if (calculation_data[i].correct_a!=calculation_data[i].correct_b)
		{
			uint64_t correct=calculation_data[i].operand1*calculation_data[i].operand2;
			printf("\n------   CALCULATION ERROR DETECTED   ------\n");
			printf(" > Iterations  \t : %08li\n"  , calculation_data[i].iterations_performed);
			printf(" > Operand 1   \t : %016lx\n" , calculation_data[i].operand1);
			printf(" > Operand 2   \t : %016lx\n" , calculation_data[i].operand2);
			printf(" > Correct     \t : %016lx\n" , calculation_data[i].operand1*calculation_data[i].operand2);
			if (correct!=calculation_data[i].correct_a)
				printf( " > Result      \t : %016lx\n" , calculation_data[i].correct_a);
			if (correct!=calculation_data[i].correct_b)
				printf( " > Result      \t : %016lx\n" , calculation_data[i].correct_b);
			printf( " > xor result  \t : %016lx\n" , calculation_data[i].correct_a^calculation_data[i].correct_b);
			char* cmd1="sensors | grep \"Core 0\" |awk '{print $3}'i | tr -d '\\n'";
			FILE *fp=popen(cmd1,"r");
			char temp[10];
			fgets(temp,10,fp);
			fclose(fp);
			printf( " > temperature \t : %s\n",temp);
			char* cmd2="cat /proc/cpuinfo | grep MHz | head -n 1 | cut  -d ':' -f2| cut -d '.' -f1 | tr -d '\\n'";
			fp=popen(cmd2,"r");
			char freq[10];
			fgets(freq,10,fp);
			printf( " > Frequency   \t :%sMHz\n",freq);
			refresh();
			fclose(fp);	
		}
	}
	printf("Done.\n");
	getch();
        return 0;
}
