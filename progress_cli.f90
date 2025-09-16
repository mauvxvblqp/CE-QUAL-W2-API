module progresscli
  use, intrinsic :: iso_fortran_env, only: output_unit
  use main,    only: tmstrt, tmend
  use screenc, only: jday, nit, eltmjd, nv
  use global,  only: dlt
  implicit none
  integer, save :: unit_log = -1
  integer, save :: last_step_printed = -1
  logical, save :: initialized = .false.
contains

  subroutine progress_init()
    character(len=10) :: cdate, cctime
    if (initialized) return
    call date_and_time(cdate, cctime)
    open(newunit=unit_log, file='w2_progress.log', status='replace', action='write')
    write(unit_log,'(A)') 'W2 run started at '//cdate//' '//cctime
    call flush(unit_log)
    initialized = .true.
    last_step_printed = -1
  end subroutine progress_init

  subroutine progress_update()
    character(len=256) :: line
    real :: percent, jd_hour, viol
    integer :: jd_int
    if (.not. initialized) call progress_init()

    if (nit == last_step_printed) return
    last_step_printed = nit

    jd_int  = int(jday)
    jd_hour = (jday - real(jd_int)) * 24.0
    if (tmend > tmstrt) then
      percent = max(0.0, min(100.0, 100.0*((jday - tmstrt)/(tmend - tmstrt))))
    else
      percent = 0.0
    end if

    if (nit > 0) then
      viol = 100.0*real(nv)/real(nit)
    else
      viol = 0.0
    end if

    write(line,'(A,I6,A,F5.2,A,F6.1,A,I8,A,F9.3,A,F6.1,A,F7.1,A)') &
         'Day ', jd_int, ' + ', jd_hour, ' h  ', percent, '% | step ', nit, ' | dt ', dlt, ' s | viol ', viol, '% | elapsed ', eltmjd, ' d'

    ! Single-line overwrite mode (previous behavior):
    ! write(output_unit,'(A)',advance='no') achar(13)//trim(line)
    ! Scrolling mode (current behavior):
    write(output_unit,'(A)') trim(line)
    call flush(output_unit)
    if (unit_log > 0) then
      write(unit_log,'(A)') trim(line)
      call flush(unit_log)
    end if
  end subroutine progress_update

  subroutine progress_finish()
    if (.not. initialized) return
    write(output_unit,'(A)') ''
    call flush(output_unit)
    if (unit_log > 0) then
      write(unit_log,'(A)') 'W2 run finished.'
      close(unit_log)
      unit_log = -1
    end if
    initialized = .false.
  end subroutine progress_finish

end module progresscli
