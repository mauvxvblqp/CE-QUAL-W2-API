module diagnosticscli
  use, intrinsic :: ieee_arithmetic
  use screenc, only: jday, eltmjd, nit
  use global
  use geomc,  only: elws
  use trans,  only: dz
  implicit none
contains
  subroutine check_nan_and_dump(stage)
    character(*), intent(in) :: stage
    logical :: has_nan
    character(len=10) :: cdate, cctime

    has_nan = .false.

    ! Sentinel checks on key state fields; if any NaN is present, dump full restart state.
    has_nan = has_nan .or. any(ieee_is_nan(U))
    has_nan = has_nan .or. any(ieee_is_nan(W))
    has_nan = has_nan .or. any(ieee_is_nan(T1))
    has_nan = has_nan .or. any(ieee_is_nan(T2))
    has_nan = has_nan .or. any(ieee_is_nan(C2))
    has_nan = has_nan .or. any(ieee_is_nan(ELWS))
    has_nan = has_nan .or. any(ieee_is_nan(RHO))
    has_nan = has_nan .or. any(ieee_is_nan(AZ))
    has_nan = has_nan .or. any(ieee_is_nan(DZ))

    if (has_nan) then
      call date_and_time(cdate, cctime)
      open(unit=99, file='w2_error.log', status='unknown', action='write', position='append')
      write(99,'(A)') repeat('=',60)
      write(99,'(A)') 'NaN detected'
      write(99,'(A,1X,A)') 'Stage:', trim(stage)
      write(99,'(A,1X,A,1X,A)') 'Wallclock:', cdate, cctime
      write(99,'(A,F10.4)') 'JDAY:', jday
      write(99,'(A,F10.4)') 'ELTMJD (elapsed days):', eltmjd
      write(99,'(A,I0)')    'NIT (step):', nit
      write(99,'(A,F10.4)') 'DLT (sec):', dlt
      write(99,'(A)') 'Writing full restart snapshot to w2_nan_rso.opt'
      close(99)

      call restart_output('w2_nan_rso.opt')

      stop 'NaN detected; see w2_error.log and w2_nan_rso.opt'
    end if
  end subroutine check_nan_and_dump

end module diagnosticscli
